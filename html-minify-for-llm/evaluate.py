import os

import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd

df = pd.read_parquet("results.parquet")

#                 model         input      cost  accuracy question_type
# 0         gpt-4o-mini           raw  0.163094       0.8  unstructured
# 1         gpt-4o-mini         clean  0.052281       0.8  unstructured
# 2         gpt-4o-mini  unstructured  0.017891       0.9  unstructured
# 3         gpt-4o-mini      markdown  0.066414       0.8  unstructured
# 4         gpt-4o-mini           raw  0.049740       0.5    structured
# 5         gpt-4o-mini         clean  0.014858       0.3    structured
# 6         gpt-4o-mini  unstructured  0.004851       0.4    structured
# 7         gpt-4o-mini      markdown  0.027072       0.1    structured
# 8   gpt-4o-2024-08-06           raw  2.718225       0.9  unstructured
# 9   gpt-4o-2024-08-06         clean  0.871350       0.9  unstructured
# 10  gpt-4o-2024-08-06  unstructured  0.298175       0.9  unstructured
# 11  gpt-4o-2024-08-06      markdown  1.106900       0.9  unstructured
# 12  gpt-4o-2024-08-06           raw  0.829000       0.8    structured
# 13  gpt-4o-2024-08-06         clean  0.247625       0.7    structured
# 14  gpt-4o-2024-08-06  unstructured  0.080850       0.7    structured
# 15  gpt-4o-2024-08-06      markdown  0.451200       0.7    structured


# Set up the plotting style
sns.set_style("whitegrid")

# Ensure plots directory exists
os.makedirs("post", exist_ok=True)

# Create a single figure with two subplots
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 8))
# Plot for unstructured questions
scatter = sns.scatterplot(
    x="cost",
    y="accuracy",
    hue="model",
    style="input",
    data=df[df["question_type"] == "unstructured"],
    ax=ax1,
    s=100,  # Increase marker size
    alpha=0.7,  # Add some transparency
)
ax1.set_title(
    "Cost vs Accuracy (Unstructured Questions)", fontsize=14, fontweight="bold"
)
ax1.set_xlabel("Cost", fontsize=12)
ax1.set_ylabel("Accuracy", fontsize=12)
ax1.grid(True, linestyle="--", alpha=0.7)
ax1.set_facecolor("#f0f0f0")  # Light gray background
ax1.set_ylim(0, 1)  # Set y-axis limit from 0 to 1


# Add a diagonal color gradient background
cmap = plt.get_cmap("RdYlGn").reversed()
x = np.linspace(0, 1, 100)
y = np.linspace(0, 1, 100)
X, Y = np.meshgrid(x, y)
Z = X + Y  # This creates a diagonal gradient from upper left to lower right
im = ax1.imshow(
    Z,
    cmap=cmap,
    extent=[ax1.get_xlim()[0], ax1.get_xlim()[1], 0, 1],
    aspect="auto",
    alpha=0.3,
    zorder=-1,
)

# Color points based on cost and accuracy
norm = plt.Normalize(df["cost"].min(), df["cost"].max())
scatter.collections[0].set_cmap(cmap)
scatter.collections[0].set_norm(norm)

# Plot for structured questions
scatter = sns.scatterplot(
    x="cost",
    y="accuracy",
    hue="model",
    style="input",
    data=df[df["question_type"] == "structured"],
    ax=ax2,
    s=100,  # Increase marker size
    alpha=0.7,  # Add some transparency
)
ax2.set_title("Cost vs Accuracy (Structured Questions)", fontsize=14, fontweight="bold")
ax2.set_xlabel("Cost", fontsize=12)
ax2.set_ylabel("Accuracy", fontsize=12)
ax2.grid(True, linestyle="--", alpha=0.7)
ax2.set_facecolor("#f0f0f0")  # Light gray background
ax2.set_ylim(0, 1)  # Set y-axis limit from 0 to 1

# Add a diagonal color gradient background
im = ax2.imshow(
    Z,
    cmap=cmap,
    extent=[ax2.get_xlim()[0], ax2.get_xlim()[1], 0, 1],
    aspect="auto",
    alpha=0.3,
    zorder=-1,
)

# Color points based on cost and accuracy
scatter.collections[0].set_cmap(cmap)
scatter.collections[0].set_norm(norm)

# Add colorbar
sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
sm.set_array([])
cbar = plt.colorbar(sm, ax=[ax1, ax2], label="Cost", pad=0.01)

# Remove the colorbar
cbar.remove()


# Adjust layout and save
plt.savefig("post/cost_vs_accuracy_comparison.png", dpi=300, bbox_inches="tight")
plt.close()

# Create a single figure with two subplots for bar plots
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 8))

# Bar plot for unstructured questions
sns.barplot(
    x="input",
    y="accuracy",
    hue="model",
    data=df[df["question_type"] == "unstructured"],
    ax=ax1,
)
ax1.set_title("Accuracy Comparison (Unstructured Questions)")
ax1.set_ylim(0, 1)
ax1.set_xlabel("Input Type")
ax1.set_ylabel("Accuracy")
ax1.tick_params(axis="x", rotation=45)

# Bar plot for structured questions
sns.barplot(
    x="input",
    y="accuracy",
    hue="model",
    data=df[df["question_type"] == "structured"],
    ax=ax2,
)
ax2.set_title("Accuracy Comparison (Structured Questions)")
ax2.set_ylim(0, 1)
ax2.set_xlabel("Input Type")
ax2.set_ylabel("Accuracy")
ax2.tick_params(axis="x", rotation=45)

# Adjust layout and save
plt.tight_layout()
plt.savefig("post/accuracy_comparison.png")
plt.close()
