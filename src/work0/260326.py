import numpy as np
import moderngl
import moderngl_window as mglw
from pyrr import Quaternion, Matrix44

class CubeSlerp(mglw.WindowConfig):
    gl_version = (3, 3)
    title = "3D Slerp: R0 (Left) -> Rt (Mid) -> R1 (Right)"
    window_size = (1280, 720)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # 顶点数据：坐标(3f) + 颜色(3f)
        vertices = np.array([
            # 前面 (蓝色)
            -0.5, -0.5,  0.5, 0, 0, 1,   0.5, -0.5,  0.5, 0, 0, 1,   0.5,  0.5,  0.5, 0, 0, 1,  -0.5,  0.5,  0.5, 0, 0, 1,
            # 后面 (绿色)
            -0.5, -0.5, -0.5, 0, 1, 0,   0.5, -0.5, -0.5, 0, 1, 0,   0.5,  0.5, -0.5, 0, 1, 0,  -0.5,  0.5, -0.5, 0, 1, 0,
            # 上面 (红色)
            -0.5,  0.5, -0.5, 1, 0, 0,   0.5,  0.5, -0.5, 1, 0, 0,   0.5,  0.5,  0.5, 1, 0, 0,  -0.5,  0.5,  0.5, 1, 0, 0,
        ], dtype='f4')
        
        indices = np.array([
            0, 1, 2, 2, 3, 0,       # 前
            4, 5, 6, 6, 7, 4,       # 后
            8, 9, 10, 10, 11, 8     # 上
        ], dtype='i4')

        self.prog = self.ctx.program(
            vertex_shader='''
                #version 330
                uniform mat4 mvp;
                in vec3 in_position;
                in vec3 in_color;
                out vec3 v_color;
                void main() {
                    gl_Position = mvp * vec4(in_position, 1.0);
                    v_color = in_color;
                }
            ''',
            fragment_shader='''
                #version 330
                in vec3 v_color;
                out vec4 f_color;
                void main() { f_color = vec4(v_color, 1.0); }
            '''
        )
        self.vbo = self.ctx.buffer(vertices)
        self.ibo = self.ctx.buffer(indices)
        self.vao = self.ctx.vertex_array(self.prog, [(self.vbo, '3f 3f', 'in_position', 'in_color')], self.ibo)

        # 定义两个旋转姿态
        self.q0 = Quaternion.from_x_rotation(0.0)
        self.q1 = Quaternion.from_x_rotation(np.pi/2) * Quaternion.from_y_rotation(np.pi/2)

    # 修复：将 render 改为 on_render
    def on_render(self, time, frame_time):
        self.ctx.clear(0.1, 0.1, 0.1)
        self.ctx.enable(moderngl.DEPTH_TEST)

        # 时间系数 t (0.0 到 1.0)
        t = (np.sin(time) + 1.0) / 2.0

        projection = Matrix44.perspective_projection(45.0, self.aspect_ratio, 0.1, 100.0)
        view = Matrix44.look_at((0, 0, 5), (0, 0, 0), (0, 1, 0))

        # 绘制三个状态的立方体
        configs = [
            (-1.5, self.q0),                      # 左：起始姿态 R0
            (0.0,  self.q0.slerp(self.q1, t)),    # 中：插值过程 Rt
            (1.5,  self.q1)                       # 右：目标姿态 R1
        ]

        for x_offset, rot_q in configs:
            model = Matrix44.from_translation((x_offset, 0, 0)) * Matrix44.from_quaternion(rot_q)
            mvp = projection * view * model
            self.prog['mvp'].write(mvp.astype('f4'))
            self.vao.render(moderngl.TRIANGLES)

if __name__ == '__main__':
    mglw.run_window_config(CubeSlerp)