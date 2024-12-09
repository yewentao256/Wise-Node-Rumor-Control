import numpy as np
import matplotlib.pyplot as plt
import random


class UndirectedGraph:
    def __init__(self, number_of_nodes):
        """Initialize the graph with the specified number of nodes."""
        self.n = number_of_nodes
        self.adj = [[] for _ in range(number_of_nodes)]

    def add_edge(self, nodeA, nodeB):
        """Add an undirected edge between nodeA and nodeB."""
        if nodeB not in self.adj[nodeA]:
            self.adj[nodeA].append(nodeB)
        if nodeA not in self.adj[nodeB]:
            self.adj[nodeB].append(nodeA)

    def edges_from(self, nodeA):
        """Return a list of all nodes connected to nodeA."""
        return self.adj[nodeA]

    def check_edge(self, nodeA, nodeB):
        """Check if there is an edge between nodeA and nodeB."""
        return nodeB in self.adj[nodeA]

    def number_of_nodes(self):
        """Return the number of nodes in the graph."""
        return self.n


def contagion_brd(
    G: UndirectedGraph, S: list, q: float, W_nodes: list = []
) -> tuple[list, list]:
    """
    Perform the BRD contagion process with optional wise nodes (W).

    Parameters:
    - G: UndirectedGraph instance.
    - S: List of initial rumor spreaders (X nodes).
    - q: Threshold for adopting the rumor.
    - W_nodes: List of wise nodes (W) that block the rumor.

    Returns:
    - infected_nodes: List of nodes infected with the rumor (X).
    - wise_nodes_final: List of nodes that became wise (W).
    """
    n = G.number_of_nodes()
    status = ["Y"] * n
    can_switch = [True] * n

    for node in S:
        status[node] = "X"
        can_switch[node] = False
    for w in W_nodes:
        status[w] = "W"
        can_switch[w] = False

    changed = True
    while changed:
        changed = False
        new_status = status.copy()
        for node in range(n):
            if not can_switch[node]:
                continue
            if status[node] == "Y":
                neighbors = G.edges_from(node)
                if len(neighbors) == 0:
                    continue
                X_count = sum(1 for neigh in neighbors if status[neigh] == "X")
                W_count = sum(1 for neigh in neighbors if status[neigh] == "W")
                ratio_X = X_count / len(neighbors)
                ratio_W = W_count / len(neighbors)

                # convert to X if rumor influence exceeds threshold
                if ratio_X >= q:
                    new_status[node] = "X"
                    changed = True
                # convert to W if wise influence exceeds threshold
                elif ratio_W >= q:
                    new_status[node] = "W"
                    changed = True
        status = new_status

    infected_nodes = [node for node in range(n) if status[node] == "X"]
    wise_nodes_final = [node for node in range(n) if status[node] == "W"]
    return infected_nodes, wise_nodes_final


def create_graph(filename="facebook_combined.txt", nodes=4039):
    """
    Create an undirected Facebook graph from the given file.

    Parameters:
    - filename: Path to the Facebook dataset file.

    Returns:
    - G: UndirectedGraph instance representing the Facebook network.
    """
    G = UndirectedGraph(nodes)
    with open(filename, "r", encoding='utf-8') as file:
        for line in file:
            parts = line.strip().split()
            if len(parts) != 2:
                continue
            nodeA, nodeB = map(int, parts)
            G.add_edge(nodeA, nodeB)
    return G


def run_experiment(
    G: UndirectedGraph, q: float, k: int, w: int, strategy: str, trials: int
) -> list:
    """
    Run the contagion experiment multiple times and collect results.

    Parameters:
    - G: UndirectedGraph instance.
    - q: Threshold for adopting the rumor.
    - k: Number of initial rumor spreaders.
    - w: Number of wise nodes.
    - strategy: Strategy for selecting wise nodes ('none', 'random', 'high_degree').
    - trials: Number of trials to run.

    Returns:
    - infected_counts: List of infected node counts for each trial.
    """
    infected_counts = []
    n = G.number_of_nodes()
    degrees = [len(G.edges_from(node)) for node in range(n)]

    for _ in range(trials):
        # select initial rumor spreaders randomly
        if k > n:
            raise ValueError(
                f"Number of initial spreaders k={k} exceeds number of nodes n={n}"
            )
        S = random.sample(range(n), k)

        # select wise nodes based on strategy
        if strategy == "none":
            W_nodes = []
        elif strategy == "random":
            available_nodes = list(set(range(n)) - set(S))
            W_nodes = random.sample(available_nodes, min(w, len(available_nodes)))
        elif strategy == "high_degree":
            sorted_nodes = sorted(range(n), key=lambda x: degrees[x], reverse=True)
            W_nodes = [node for node in sorted_nodes if node not in S][:w]
        else:
            raise ValueError("Unknown strategy")

        # run the contagion process
        infected, _ = contagion_brd(G, S, q, W_nodes)
        infected_counts.append(len(infected))
    return infected_counts


def main():
    # Parameters
    # The dataset is from: https://github.com/benedekrozemberczki/MUSAE
    # 22,470 nodes with 171,002 edges
    filename = "musae_facebook.txt"
    q = 0.1  # Threshold for adopting the rumor
    k_values = [10, 100, 1000, 10000]   # initial rumor spreaders
    w_values = [0, 5, 10, 20, 50, 100]  # initial numbers of wise nodes
    trials = 10                         # number of trials for averaging

    print("Loading graph...")
    G = create_graph(filename, 22470)
    print("graph loaded.")

    # Define strategies
    strategies = ["random", "high_degree"]
    strategy_labels = {
        "random": "Random Wise Nodes",
        "high_degree": "High-Degree Wise Nodes",
    }
    strategy_colors = {"random": "green", "high_degree": "red"}

    # iterate over each k value
    for k in k_values:
        print(f"\nRunning experiments for k={k} initial rumor spreaders...")
        plt.figure(figsize=(12, 8))

        # iterate over each strategy
        for strategy in strategies:
            average_infected = []
            std_devs = []
            print(f"  Strategy: {strategy_labels[strategy]}")

            # iterate over each w value
            for w in w_values:
                print(f"    Number of Wise Nodes (w): {w}")
                infected_counts = run_experiment(G, q, k, w, strategy, trials)
                avg = np.mean(infected_counts)
                std = np.std(infected_counts)
                average_infected.append(avg)
                std_devs.append(std)
                print(f"      Average infected: {avg:.2f}, Std Dev: {std:.2f}")

            # plot the results for the current strategy
            plt.errorbar(
                w_values,
                average_infected,
                yerr=std_devs,
                label=strategy_labels[strategy],
                color=strategy_colors[strategy],
                marker="o",
                capsize=5,
            )

        # customize the plot
        plt.xlabel("Number of Wise Nodes (w)", fontsize=14)
        plt.ylabel("Average Number of Infected Nodes", fontsize=14)
        plt.title(
            f"Impact of Wise Node Selection Strategies on Rumor Spread (k={k})",
            fontsize=16,
        )
        plt.legend(fontsize=12)
        plt.grid(True, linestyle="--", alpha=0.7)
        plt.xticks(w_values)
        plt.tight_layout()

        plot_filename = f"rumor_spread_k{k}.png"
        plt.savefig(plot_filename)
        print(f"  Plot saved as {plot_filename}")


if __name__ == "__main__":
    main()
