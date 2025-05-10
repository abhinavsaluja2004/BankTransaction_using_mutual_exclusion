
# Bank Transaction Simulation Using Distributed Mutual Exclusion

This project simulates **distributed bank transactions** using **mutual exclusion algorithms**. Initially implemented with the **Ricart-Agrawala algorithm**, the project has been **optimized using the Roucairol-Carvalho algorithm** and a **quorum-based approach** to enhance efficiency and reduce message overhead.

> **Inspired by:**  
> [Bea2000/Distributed-Systems-Task-Ricart-Agrawala-Algorithm-for-Bank-Transactions-T1](https://github.com/Bea2000/Distributed-Systems-Task-Ricart-Agrawala-Algorithm-for-Bank-Transactions-T1)

---

## 🧠 Algorithms Implemented

- **Ricart-Agrawala Algorithm**: Ensures mutual exclusion via message-passing between distributed processes.
- **Rouçairol-Carvalho Optimization**: Reduces redundant communication by not releasing permissions unnecessarily.
- **Quorum-based Mutual Exclusion**: Minimizes the number of nodes a process must coordinate with, improving scalability.

---

## 🛠 Why Go?

We used **Go (Golang)** because:
- It supports **concurrent programming** natively using goroutines and channels.
- It is **lightweight and fast**, ideal for networked and distributed applications.
- Built-in packages make handling **network communication**, **JSON**, and **timing** simple and efficient.

---

## 📁 File Structure and Descriptions

| File | Description |
|------|-------------|
| `main.go` | Core logic for simulating bank transactions using mutual exclusion algorithms. Implements Ricart-Agrawala, Roucairol-Carvalho optimization, and quorum-based enhancements. |
| `main_og.go` | Original unoptimized version using only the Ricart-Agrawala algorithm. |
| `performance_metrics.go` | Records and analyzes metrics such as message counts and execution time for various algorithms. |
| `visualize_metrics.py` | Python script to generate visual plots for performance metrics. |
| `visualize_metrics_workloads.py` | Python script to plot performance under varying workloads. |
| `run_tests.sh` | Shell script for Linux users to compile and test the Go code. |
| `run_tests.ps1` | PowerShell script for Windows users to compile and run the code. |
| `logs.txt` / `logs_og.txt` | Captures runtime logs for optimized and original versions, respectively. |
| `final.txt` / `final_og.txt` | Summarized output results for optimized and original versions. |

---

## 🚀 Getting Started

### 🔧 Prerequisites
- Install **Go compiler** (https://golang.org/dl/)
- (Optional) Python with `matplotlib` and `pandas` for visualization

### ▶️ Running the Simulation

#### For **Linux**:
```bash
chmod +x run_tests.sh
./run_tests.sh
```

#### For **Windows** (PowerShell):
```powershell
./run_tests.ps1
```

---

## 📊 Visualization

To generate performance graphs:
```bash
python3 visualize_metrics.py
python3 visualize_metrics_workloads.py
```

---

## 🤝 Acknowledgments

This project is based on the work done in the [Distributed-Systems-Task-Ricart-Agrawala](https://github.com/Bea2000/Distributed-Systems-Task-Ricart-Agrawala-Algorithm-for-Bank-Transactions-T1) repository. Thanks to the original authors for the foundational implementation.

---

## 📌 Notes

- Make sure your **Go environment** is set up correctly (`$GOPATH`, `$GOROOT` if needed).
- The simulation assumes nodes can communicate using local ports and are run in parallel.

---

## 📞 Contact

For questions or suggestions, feel free to reach out via [GitHub Issues](https://github.com/abhinavsaluja2004/BankTransaction_using_mutual_exclusion/issues).
