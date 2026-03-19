import taichi as ti
import math

# 初始化 Taichi
ti.init(arch=ti.cpu)

# --- 1. 定义数据结构 ---
# 立方体有 8 个顶点
num_vertices = 8
# 立方体有 12 条边
num_edges = 12

vertices = ti.Vector.field(3, dtype=ti.f32, shape=num_vertices)
screen_coords = ti.Vector.field(2, dtype=ti.f32, shape=num_vertices)

# 存储边的索引对：例如 (0, 1) 表示顶点0和顶点1连成一条线
edges = ti.field(dtype=ti.i32, shape=(num_edges, 2))

@ti.func
def get_model_matrix(angle: ti.f32):
    """
    模型变换矩阵：改为绕 Y 轴旋转，立体感更强
    """
    rad = angle * math.pi / 180.0
    c = ti.cos(rad)
    s = ti.sin(rad)
    return ti.Matrix([
        [ c,  0.0,  s,  0.0],
        [ 0.0, 1.0,  0.0, 0.0],
        [-s,  0.0,  c,  0.0],
        [ 0.0, 0.0,  0.0, 1.0]
    ])

@ti.func
def get_view_matrix(eye_pos):
    return ti.Matrix([
        [1.0, 0.0, 0.0, -eye_pos[0]],
        [0.0, 1.0, 0.0, -eye_pos[1]],
        [0.0, 0.0, 1.0, -eye_pos[2]],
        [0.0, 0.0, 0.0, 1.0]
    ])

@ti.func
def get_projection_matrix(eye_fov: ti.f32, aspect_ratio: ti.f32, zNear: ti.f32, zFar: ti.f32):
    # 透视投影：将平截头体变换为正则观察体
    fov_rad = eye_fov * math.pi / 180.0
    tan_half_fov = ti.tan(fov_rad / 2.0)
    
    # 这是一个标准的 OpenGL 风格透视投影矩阵简化版
    # 重点在于利用 z 处理缩放，并实现“近大远小”
    return ti.Matrix([
        [1.0 / (aspect_ratio * tan_half_fov), 0.0, 0.0, 0.0],
        [0.0, 1.0 / tan_half_fov, 0.0, 0.0],
        [0.0, 0.0, -(zFar + zNear) / (zFar - zNear), -(2.0 * zFar * zNear) / (zFar - zNear)],
        [0.0, 0.0, -1.0, 0.0]
    ])

@ti.kernel
def compute_transform(angle: ti.f32):
    eye_pos = ti.Vector([0.0, 0.0, 5.0])
    model = get_model_matrix(angle)
    view = get_view_matrix(eye_pos)
    proj = get_projection_matrix(45.0, 1.0, 0.1, 50.0)
    
    mvp = proj @ view @ model
    
    for i in range(num_vertices):
        v4 = ti.Vector([vertices[i][0], vertices[i][1], vertices[i][2], 1.0])
        v_clip = mvp @ v4
        
        # 透视除法
        v_ndc = v_clip / v_clip[3]
        
        # 视口变换
        screen_coords[i][0] = (v_ndc[0] + 1.0) / 2.0
        screen_coords[i][1] = (v_ndc[1] + 1.0) / 2.0

def init_cube():
    # 定义 8 个顶点 (范围 -1 到 1)
    v_data = [
        [-1, -1,  1], [ 1, -1,  1], [ 1,  1,  1], [-1,  1,  1],
        [-1, -1, -1], [ 1, -1, -1], [ 1,  1, -1], [-1,  1, -1]
    ]
    for i in range(8):
        vertices[i] = v_data[i]

    # 定义 12 条边
    e_data = [
        [0, 1], [1, 2], [2, 3], [3, 0], # 底面
        [4, 5], [5, 6], [6, 7], [7, 4], # 顶面
        [0, 4], [1, 5], [2, 6], [3, 7]  # 侧柱
    ]
    for i in range(12):
        edges[i, 0] = e_data[i][0]
        edges[i, 1] = e_data[i][1]

def main():
    init_cube()
    gui = ti.GUI("3D Cube Rotation (Taichi)", res=(700, 700))
    angle = 0.0
    
    while gui.running:
        # 自动持续旋转，也可保留 A/D 键控制
        angle += 1.0 
        
        if gui.get_event(ti.GUI.PRESS):
            if gui.event.key == ti.GUI.ESCAPE:
                gui.running = False
        
        compute_transform(angle)
        
        # 遍历边进行绘制
        for i in range(num_edges):
            idx1 = edges[i, 0]
            idx2 = edges[i, 1]
            gui.line(screen_coords[idx1], screen_coords[idx2], radius=2, color=0x00FF00)
        
        gui.show()

if __name__ == '__main__':
    main()