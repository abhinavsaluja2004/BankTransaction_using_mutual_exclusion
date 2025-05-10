package main

import (
	"encoding/json"
	"fmt"
	"os"
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

// Add this to your existing Request, Account, and Message types...

func (account *Account) sendRequest(request Request, accounts []Account) {
	// Count outgoing requests
	var sentCount int64 = 0

	// Use appropriate request sending logic based on algorithm type
	if useQuorum {
		// Quorum + RC optimization: send request only to accounts not in outstandingPermit
		// and only to accounts in the quorum
		for _, qid := range account.quorum {
			if qid != account.id && !account.outstandingPermit[qid] {
				requestChannels[qid] <- request
				sentCount++
			}
		}
	} else {
		// Original algorithm: send to all other accounts
		for i := 0; i < len(accounts); i++ {
			if i != account.id {
				requestChannels[i] <- request
				sentCount++
			}
		}
	}

	// Update metrics
	atomic.AddInt64(&totalRequests, sentCount)
}

func (account *Account) approveRequest(request Request) {
	// Send an approval to the account that made the request
	approveChannels[request.id] <- account.id

	// Update metrics
	atomic.AddInt64(&totalApprovals, 1)
}

func waitForApproval(account *Account, accounts []Account) {
	if useQuorum {
		// Quorum-based waiting
		needed := 0
		for _, qid := range account.quorum {
			if qid != account.id && !account.outstandingPermit[qid] {
				needed++
			}
		}

		// Wait for the needed approvals
		for i := 0; i < needed; i++ {
			approverID := <-approveChannels[account.id]
			account.outstandingPermit[approverID] = true
		}
	} else {
		// Original: wait for all accounts to approve
		for i := 0; i < len(accounts)-1; i++ {
			<-approveChannels[account.id]
		}
	}
}

// Add a flag to switch between algorithms
var useQuorum bool

func main() {
	// Parse command line arguments
	if len(os.Args) < 3 {
		fmt.Println("Usage: go run main.go <folder_name> <algorithm>")
		fmt.Println("  algorithm: 'original' or 'optimized'")
		return
	}

	folder_name := os.Args[1]
	algorithm := os.Args[2]

	// Set algorithm flag
	useQuorum = (algorithm == "optimized")

	// Reset metrics
	totalRequests = 0
	totalApprovals = 0
	startTime = time.Now()

	os.Remove("logs.txt")

	// Run the algorithm
	accounts, messages := readTransactions(folder_name)

	// Create channels for sending requests, approvals, and messages
	createChannels(accounts)

	// Set up request handling goroutines
	for i := range accounts {
		go func(account *Account) {
			for request := range requestChannels[account.id] {
				account.receiveRequest(request)
			}
		}(&accounts[i])
	}

	// Process initial bank transactions
	for i := range accounts {
		registerTransaction(messages[i])
	}

	// Process all transactions
	var wg sync.WaitGroup
	for i := range accounts {
		wg.Add(1)
		go func(account *Account) {
			account.processTransaction(messages, accounts, &wg)
		}(&accounts[i])
	}

	// Wait for all goroutines to finish
	wg.Wait()

	// Calculate total duration
	totalDuration = time.Since(startTime).Milliseconds()

	// Register the final balances
	registerFinalBalances(accounts)

	// Output metrics
	outputMetrics(accounts, messages, algorithm)
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
