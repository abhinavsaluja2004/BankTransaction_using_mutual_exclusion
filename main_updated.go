package main

import (
	"bufio"
	"encoding/json"
	"fmt"
	"os"
	"strconv"
	"strings"
	"sync"
	"sync/atomic"
	"time"
)

// Global counters for message metrics
var (
	totalRequests  int64
	totalApprovals int64
	startTime      time.Time
	totalDuration  int64 // in milliseconds
)

// Metrics structure for JSON output
type Metrics struct {
	Algorithm     string `json:"algorithm"`
	Accounts      int    `json:"accounts"`
	Transactions  int    `json:"transactions"`
	Requests      int64  `json:"requests"`
	Approvals     int64  `json:"approvals"`
	TotalMessages int64  `json:"totalMessages"`
	Duration      int64  `json:"durationMs"`
}

type Request struct {
	// a request to enter the critical section
	turn int
	id   int
}

type Account struct {
	// an account in the bank
	id                int
	turn              int
	highestTurn       int
	requestCS         bool
	last_message_id   int
	deferred_queue    []Request
	deferred_mutex    sync.Mutex
	outstandingPermit map[int]bool // RC optimization: keep track of permissions
	quorum            []int        // Quorum-based communication: list of accounts needed for approval
}

type Message struct {
	// a message sent between accounts only when they are in the critical section
	from  int
	money int
	to    int
	time  int
}

// a map of channels for sending requests to enter the critical section
var requestChannels = make(map[int]chan Request)

// a map of channels for sending approvals to enter the critical section
var approveChannels = make(map[int]chan int)

func createChannels(accounts []Account) {
	// create a channel for sending requests to enter the critical section
	for i := range accounts {
		requestChannels[i] = make(chan Request)
		approveChannels[i] = make(chan int)
	}
}

func NewAccount(id int, quorum []int) Account {
	// create a new account with the given id and quorum
	return Account{
		id:                id,
		turn:              0,
		highestTurn:       0,
		requestCS:         false,
		deferred_queue:    make([]Request, 0),
		last_message_id:   0,
		outstandingPermit: make(map[int]bool),
		quorum:            quorum,
	}
}

func (account *Account) NewRequest() Request {
	// create a new request with the given turn and id
	return Request{
		turn: account.turn,
		id:   account.id,
	}
}

func (account *Account) sendRequest(request Request, accounts []Account) {
	// RC optimization: send request only to accounts not in outstandingPermit
	// and only to accounts in the quorum
	var sentCount int64 = 0

	for _, qid := range account.quorum {
		if qid != account.id && !account.outstandingPermit[qid] {
			requestChannels[qid] <- request
			sentCount++
		}
	}

	// Update metrics
	atomic.AddInt64(&totalRequests, sentCount)
}

func (account *Account) approveRequest(request Request) {
	// send an approval to the account that made the request
	approveChannels[request.id] <- account.id

	// Update metrics
	atomic.AddInt64(&totalApprovals, 1)
}

func waitForApproval(account *Account) {
	// wait for approvals from quorum members we don't have permission from
	needed := 0
	for _, qid := range account.quorum {
		if qid != account.id && !account.outstandingPermit[qid] {
			needed++
		}
	}

	// wait for the needed approvals
	for i := 0; i < needed; i++ {
		approverID := <-approveChannels[account.id]
		account.outstandingPermit[approverID] = true
	}
}

func (account *Account) askCS(request Request, accounts []Account) {
	// ask to enter the critical section
	account.turn += account.highestTurn + 1
	request.turn = account.turn
	account.requestCS = true
	account.sendRequest(request, accounts)
	waitForApproval(account)
}

func (account *Account) releaseCS() {
	// release the critical section
	account.requestCS = false
	account.deferred_mutex.Lock()
	for len(account.deferred_queue) > 0 {
		request := account.deferred_queue[0]
		account.deferred_queue = account.deferred_queue[1:]
		account.approveRequest(request)
		// RC optimization: we no longer have permission from this account
		account.outstandingPermit[request.id] = false
	}
	account.deferred_mutex.Unlock()
}

func (account *Account) receiveRequest(request Request) {
	// receive a request to enter the critical section
	// change highetsTurn to the highest turn received
	if request.turn > account.highestTurn {
		account.highestTurn = request.turn
	}

	if !account.requestCS || (request.turn < account.turn) || (request.turn == account.turn && request.id < account.id) {
		account.approveRequest(request)
	} else {
		account.deferred_mutex.Lock()
		account.deferred_queue = append(account.deferred_queue, request)
		account.deferred_mutex.Unlock()
	}
}

func registerFinalBalances(accounts []Account) {
	// create a file to write the final balances of the accounts
	file, err := os.Create("final.txt")
	if err != nil {
		fmt.Println(err)
		return
	}
	defer file.Close()

	for i := 0; i < len(accounts); i++ {
		total_money := checkAvailableMoney(i)
		file.WriteString(fmt.Sprintf("%d,%d\n", i, total_money))
	}
}

func registerTransaction(message Message) {
	file, err := os.OpenFile("logs.txt", os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)

	if err != nil {
		fmt.Println("error opening transaction file:", err)
		return
	}
	defer file.Close()

	file.WriteString(fmt.Sprintf("Participant %d has transferred %d to participant %d.\n", message.from, message.money, message.to))
}

func checkAvailableMoney(id int) int {
	var final_money int = 0
	file, err := os.Open("logs.txt")
	if err != nil {
		fmt.Println(err)
	}
	defer file.Close()

	// check all transactions that involve the account with the given id
	scanner := bufio.NewScanner(file)
	for scanner.Scan() {
		line := scanner.Text()
		parts := strings.Split(line, " ")
		if len(parts) < 8 {
			fmt.Println("Incorrect line format:", line)
			continue
		}

		from_str := strings.TrimPrefix(parts[1], "Participante")
		from, err := strconv.Atoi(from_str)
		if err != nil {
			fmt.Println("Error parsing participant 1:", err)
			continue
		}

		money_str := strings.TrimPrefix(parts[4], "$")
		money, err := strconv.Atoi(money_str)
		if err != nil {
			fmt.Println("Error parsing money:", err)
			continue
		}

		to_str := strings.TrimPrefix(parts[7], "participante")
		to_str = strings.TrimSuffix(to_str, ".")
		to, err := strconv.Atoi(to_str)
		if err != nil {
			fmt.Println("Error parsing participant 2:", err)
			continue
		}

		if from == id {
			final_money -= money
		} else if to == id {
			final_money += money
		}
	}

	if err := scanner.Err(); err != nil {
		fmt.Println("Error reading file:", err)
	}

	return final_money
}

func readTransactions(folder_name string) ([]Account, []Message) {
	// Open the transactions file
	file, err := os.Open(folder_name + "/transactions.txt")
	if err != nil {
		// Try with Spanish filename if English one doesn't exist
		file, err = os.Open(folder_name + "/transacciones.txt")
		if err != nil {
			fmt.Println(err)
			return nil, nil
		}
	}
	defer file.Close()

	// Create a scanner to read the file line by line
	scanner := bufio.NewScanner(file)

	// Read the first line containing the number of accounts and transactions
	scanner.Scan()
	firstLine := scanner.Text()
	parts := strings.Split(firstLine, ",")
	n_accounts, _ := strconv.Atoi(parts[0])
	m_transactions, _ := strconv.Atoi(parts[1])

	// Read quorums from quorum.txt
	quorums := readQuorums(folder_name, n_accounts)

	// Create the account array
	var accounts = make([]Account, n_accounts)
	for i := 0; i < n_accounts; i++ {
		accounts[i] = NewAccount(i, quorums[i])
	}

	// Create the transaction (message) array
	var messages = make([]Message, m_transactions)

	// Read the rest of the lines containing the transactions
	i := 0
	for scanner.Scan() {
		line := scanner.Text()
		parts := strings.Split(line, ",")
		from, _ := strconv.Atoi(parts[0])
		money, _ := strconv.Atoi(parts[1])
		to, _ := strconv.Atoi(parts[2])
		time, _ := strconv.Atoi(parts[3])

		messages[i] = Message{
			from:  from,
			to:    to,
			money: money,
			time:  time,
		}

		i++
	}

	if err := scanner.Err(); err != nil {
		fmt.Println("Error reading file:", err)
	}

	return accounts, messages
}

func readQuorums(folder_name string, n_accounts int) [][]int {
	// Read quorums from quorum.txt
	quorums := make([][]int, n_accounts)

	// Open the quorum file
	file, err := os.Open(folder_name + "/quorum.txt")
	if err != nil {
		fmt.Println("Error opening quorum file:", err)
		// If quorum file doesn't exist, create default quorums (all accounts need to approve)
		for i := 0; i < n_accounts; i++ {
			quorums[i] = make([]int, n_accounts)
			for j := 0; j < n_accounts; j++ {
				quorums[i][j] = j
			}
		}
		return quorums
	}
	defer file.Close()

	// Create a scanner to read the file line by line
	scanner := bufio.NewScanner(file)

	// Read quorums for each account
	for i := 0; i < n_accounts; i++ {
		if !scanner.Scan() {
			fmt.Println("Error reading quorum for account", i)
			// If quorum is not specified, default to all accounts
			quorums[i] = make([]int, n_accounts)
			for j := 0; j < n_accounts; j++ {
				quorums[i][j] = j
			}
			continue
		}

		line := scanner.Text()
		parts := strings.Split(line, ",")
		quorum := make([]int, len(parts))
		for j, part := range parts {
			quorum[j], _ = strconv.Atoi(part)
		}
		quorums[i] = quorum
	}

	if err := scanner.Err(); err != nil {
		fmt.Println("Error reading quorum file:", err)
	}

	return quorums
}

func (account *Account) processTransaction(messages []Message, accounts []Account, wg *sync.WaitGroup) {
	defer wg.Done()
	for i := account.last_message_id + 1; i < len(messages); i++ {
		message := messages[i]
		if message.from == account.id {
			account.last_message_id = i
			account.askCS(account.NewRequest(), accounts)

			if checkAvailableMoney(account.id) < message.money {
				account.releaseCS()
				for checkAvailableMoney(account.id) < message.money {
					// Wait until account has enough money
					time.Sleep(10 * time.Millisecond)
				}
				account.askCS(account.NewRequest(), accounts)
			}

			registerTransaction(message)
			account.releaseCS()

			if message.time > 0 {
				time.Sleep(time.Duration(message.time) * time.Millisecond)
			}
		}
	}
}

func outputMetrics(accounts []Account, messages []Message, algorithm string) {
	metrics := Metrics{
		Algorithm:     algorithm,
		Accounts:      len(accounts),
		Transactions:  len(messages),
		Requests:      totalRequests,
		Approvals:     totalApprovals,
		TotalMessages: totalRequests + totalApprovals,
		Duration:      totalDuration,
	}

	// Output as JSON
	data, err := json.MarshalIndent(metrics, "", "  ")
	if err != nil {
		fmt.Println("Error creating JSON:", err)
		return
	}

	// Write to metrics file
	outFile := fmt.Sprintf("metrics_%s.json", algorithm)
	err = os.WriteFile(outFile, data, 0644)
	if err != nil {
		fmt.Println("Error writing metrics file:", err)
		return
	}

	fmt.Println("Performance metrics saved to", outFile)
	fmt.Printf("\nAlgorithm: %s\n", algorithm)
	fmt.Printf("Number of accounts: %d\n", len(accounts))
	fmt.Printf("Number of transactions: %d\n", len(messages))
	fmt.Printf("Request messages sent: %d\n", totalRequests)
	fmt.Printf("Approval messages sent: %d\n", totalApprovals)
	fmt.Printf("Total messages: %d\n", totalRequests+totalApprovals)
	fmt.Printf("Total duration: %d ms\n", totalDuration)
}

func main() {
	// Get algorithm type from command line
	algorithm := "optimized"
	if len(os.Args) > 2 {
		algorithm = os.Args[2]
	}

	// Reset metrics
	totalRequests = 0
	totalApprovals = 0
	startTime = time.Now()

	os.Remove("logs.txt")
	folder_name := "tests/test_5"

	// Use command line argument for folder if provided
	if len(os.Args) > 1 {
		folder_name = os.Args[1]
	}

	accounts, messages := readTransactions(folder_name)

	// create channels for sending requests, approvals, and messages
	createChannels(accounts)

	// create a goroutine for each account for process receive requests
	for i := range accounts {
		go func(account *Account) {
			for request := range requestChannels[account.id] {
				account.receiveRequest(request)
			}
		}(&accounts[i])
	}

	// process bank transactions
	for i := range accounts {
		registerTransaction(messages[i])
	}

	// create a wait group to wait for all goroutines to finish
	var wg sync.WaitGroup

	// create a goroutine for each account for process messages
	for i := range accounts {
		wg.Add(1)
		go func(account *Account) {
			account.processTransaction(messages, accounts, &wg)
		}(&accounts[i])
	}

	// wait for all goroutines to finish
	wg.Wait()

	// Calculate total duration
	totalDuration = time.Since(startTime).Milliseconds()

	// register the final balances of the accounts
	registerFinalBalances(accounts)

	// Output metrics
	outputMetrics(accounts, messages, algorithm)
}
