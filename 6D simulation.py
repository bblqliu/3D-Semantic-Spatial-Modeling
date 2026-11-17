import numpy as np
import matplotlib.pyplot as plt

# 设置学术论文绘图风格 (支持高分辨率与衬线字体)
plt.rcParams.update({
    "font.family": "serif",
    "font.size": 10,
    "axes.labelsize": 11,
    "axes.titlesize": 11,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "legend.fontsize": 9,
    "figure.dpi": 300
})

# ==============================================================================
# 仿真程序 1：图1（不同遮挡率下的6D位姿平移误差仿真）
# ==============================================================================
def simulate_pose_error():
    occlusion_ratios = np.array([0, 20, 40, 60, 80])
    # 模拟不同视觉遮挡率下的6D位姿平移误差数据 (mm)
    vision_only_trans = np.array([4.2, 9.8, 18.6, 31.4, 45.2])
    static_fusion_trans = np.array([3.1, 5.2, 8.4, 14.1, 21.3])
    ours_trans = np.array([1.8, 2.3, 3.2, 4.0, 4.9])

    plt.figure(figsize=(6, 3.8))
    plt.plot(occlusion_ratios, vision_only_trans, 's--', color='#d95f02', linewidth=1.8, label='Vision-Only Baseline')
    plt.plot(occlusion_ratios, static_fusion_trans, '^-.', color='#7570b3', linewidth=1.8, label='Static Visuo-Tactile')
    plt.plot(occlusion_ratios, ours_trans, 'o-', color='#1b9e77', linewidth=2.2, label='Ours (Active Probing + SE(3))')
    
    plt.title('6D Pose Translation Error under Visual Occlusions')
    plt.xlabel('Visual Occlusion Ratio (%)')
    plt.ylabel('Translation Error (mm)')
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.legend(frameon=True, facecolor='white', edgecolor='none')
    plt.tight_layout()
    plt.savefig('fig1_pose_error.png', bbox_inches='tight')
    plt.close()
    print("-> 图1 (fig1_pose_error.png) 生成成功。")

# ==============================================================================
# 仿真程序 2：图2（主动触觉探查过程中的信息熵与Chamfer距离收敛仿真）
# ==============================================================================
def simulate_entropy_convergence():
    probing_steps = np.arange(0, 11)
    # 模拟高斯过程（GP）空间微分熵与网格Chamfer距离随探查步数的衰减指数曲线
    mean_entropy = 4.82 * np.exp(-0.45 * probing_steps) + 0.1
    surface_chamfer = 12.4 * np.exp(-0.4 * probing_steps) + 0.6

    fig, ax1 = plt.subplots(figsize=(6, 3.8))
    color = '#d95f02'
    ax1.set_xlabel('Active Probing Iteration Step ($N_{probe}$)')
    ax1.set_ylabel('Mean Surface Entropy $H(x)$ (nats)', color=color)
    line1 = ax1.plot(probing_steps, mean_entropy, 'o-', color=color, linewidth=1.8, label='Surface Entropy')
    ax1.tick_params(axis='y', labelcolor=color)
    ax1.set_ylim(0, 5.5)

    ax2 = ax1.twinx()  
    color = '#377eb8'
    ax2.set_ylabel('Chamfer Distance (mm)', color=color)
    line2 = ax2.plot(probing_steps, surface_chamfer, 's--', color=color, linewidth=1.8, label='Chamfer Distance')
    ax2.tick_params(axis='y', labelcolor=color)
    ax2.set_ylim(0, 14)

    lines = line1 + line2
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc='upper right', frameon=True)
    
    plt.title('Uncertainty Reduction via Active Tactile Probing')
    plt.grid(True, linestyle=':', alpha=0.4)
    plt.tight_layout()
    plt.savefig('fig2_entropy_convergence.png', bbox_inches='tight')
    plt.close()
    print("-> 图2 (fig2_entropy_convergence.png) 生成成功。")

# ==============================================================================
# 仿真程序 3：图3（开放词汇3D语义特征对齐雷达图仿真）
# ==============================================================================
def simulate_semantic_radar():
    categories = ['Bottle', 'Mug Handle', 'Foam Box', 'Flask Rim', 'Metal Bolt']
    # 模拟纯视觉与视触觉融合在不同几何区域上的语义特征对齐余弦相似度
    vis_only_sim = [0.88, 0.42, 0.76, 0.31, 0.45]
    vis_tac_sim = [0.94, 0.91, 0.93, 0.89, 0.92]

    N = len(categories)
    angles = [n / float(N) * 2 * np.pi for n in range(N)]
    angles += angles[:1]
    
    vis_only_sim_closed = vis_only_sim + vis_only_sim[:1]
    vis_tac_sim_closed = vis_tac_sim + vis_tac_sim[:1]

    plt.figure(figsize=(6, 4.2))
    ax = plt.subplot(111, polar=True)
    plt.xticks(angles[:-1], categories, size=10)
    ax.set_rlabel_position(30)
    plt.yticks([0.2, 0.4, 0.6, 0.8, 1.0], ["0.2", "0.4", "0.6", "0.8", "1.0"], color="grey", size=8)
    plt.ylim(0, 1.05)

    ax.plot(angles, vis_only_sim_closed, 'o--', linewidth=1.8, color='#e7298a', label='Visual-Only Feature Field')
    ax.fill(angles, vis_only_sim_closed, color='#e7298a', alpha=0.15)

    ax.plot(angles, vis_tac_sim_closed, 'o-', linewidth=2.2, color='#66a61e', label='Ours (Visuo-Tactile Fusion)')
    ax.fill(angles, vis_tac_sim_closed, color='#66a61e', alpha=0.25)

    plt.title('Open-Vocabulary 3D Semantic Alignment Profile (Radar)', y=1.08)
    plt.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), frameon=True)
    plt.tight_layout()
    plt.savefig('fig3_semantic_radar.png', bbox_inches='tight')
    plt.close()
    print("-> 图3 (fig3_semantic_radar.png) 生成成功。")

if __name__ == "__main__":
    print("开始运行仿真绘图程序...")
    simulate_pose_error()
    simulate_entropy_convergence()
    simulate_semantic_radar()
    print("所有图表仿真程序执行完毕！")