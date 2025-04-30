import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import matplotlib

# 设置中文字体（避免中文乱码）
matplotlib.rcParams['font.sans-serif'] = ['STHeiti', 'Songti SC', 'Heiti TC', 'LiSong Pro', 'SimHei']
matplotlib.rcParams['axes.unicode_minus'] = False

# 生成时间序列（0-36个月）
x = np.linspace(0, 36, 360)

# 定义各阶段函数（逻辑斯蒂增长模型模拟自然流量）
def logistic_growth(t, K, r, t0):
    return K / (1 + np.exp(-r*(t - t0)))

# 参数设置
K = 10000  # 最大流量（稳定期上限）
r1 = 0.1   # 积累期增长率
r2 = 0.3   # 爆发期增长率
t01 = 12   # 拐点时间（12个月）
t02 = 24   # 爆发期开始时间

# 分段生成流量数据
y_accumulate = logistic_growth(x[x<t01], K, r1, t01/2)  # 积累期（0-12个月）
y_turn = logistic_growth(x[(x>=t01)&(x<t02)], K, r2, t01)  # 拐点期（12-24个月）
y_explode = logistic_growth(x[x>=t02], K, r2, t02)  # 爆发期+稳定期（24个月后）

# 合并数据
y = np.concatenate((y_accumulate, y_turn, y_explode))

# 绘制图形
plt.figure(figsize=(10, 6))

# 主曲线
plt.plot(x, y, label='自然流量增长曲线', color='#2c3e50', linewidth=2.5)

# 标注关键节点
plt.scatter([12, 24], [logistic_growth(12, K, r1, t01/2), logistic_growth(24, K, r2, t02)], 
            color='#e74c3c', s=100, marker='*')
plt.text(12, logistic_growth(12, K, r1, t01/2)+800, '内容积累拐点', ha='center', va='bottom', fontsize=10)
plt.text(24, logistic_growth(24, K, r2, t02)+1200, '爆发期起点', ha='center', va='bottom', fontsize=10)

# 阶段划分阴影
plt.axvspan(0, 12, alpha=0.1, color='#3498db', label='积累期（0-12个月）')
plt.axvspan(12, 24, alpha=0.1, color='#f1c40f', label='拐点期（12-24个月）')
plt.axvspan(24, 36, alpha=0.1, color='#2ecc71', label='爆发期（24个月后）')

# 添加注释
plt.text(6, K*0.3, '持续输出优质内容\n积累SEO权重', ha='center', va='center', fontsize=10,
         bbox=dict(facecolor='white', alpha=0.8))
plt.text(18, K*0.6, '长尾效应显现\n老内容持续获客', ha='center', va='center', fontsize=10,
         bbox=dict(facecolor='white', alpha=0.8))
plt.text(30, K*0.9, '内容矩阵协同\n品牌信任形成', ha='center', va='center', fontsize=10,
         bbox=dict(facecolor='white', alpha=0.8))

# 图表设置
plt.xlabel('时间（月）', fontsize=12)
plt.ylabel('自然流量（访问量）', fontsize=12)
plt.title('自然流量增长曲线图示', fontsize=14, fontweight='bold')
plt.legend(loc='lower right', fontsize=10)
plt.grid(True, linestyle='--', alpha=0.7)
plt.xlim(0, 36)
plt.ylim(0, K*1.1)

# 显示图形
plt.tight_layout()
plt.show()

# 打印可用字体
print([f.name for f in fm.fontManager.ttflist if 'Hei' in f.name or 'Song' in f.name or 'Gothic' in f.name])