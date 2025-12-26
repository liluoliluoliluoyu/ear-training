# 个人网站

一个现代化的个人网站，具有响应式设计和丰富的交互功能。

## 功能特性

- 🎨 现代化的UI设计
- 📱 完全响应式布局
- ⚡ 流畅的动画效果
- 🎯 平滑滚动导航
- 📧 联系表单
- 🌙 优雅的视觉效果
- ♿ 无障碍访问支持

## 技术栈

- HTML5
- CSS3 (Flexbox, Grid, 动画)
- JavaScript (ES6+)
- Font Awesome 图标
- 响应式设计

## 快速开始

### 方法一：使用Python内置服务器

```bash
# 启动开发服务器
npm start
# 或者
python3 -m http.server 8000
```

然后在浏览器中访问 `http://localhost:8000`

### 方法二：使用其他静态服务器

```bash
# 使用Node.js的http-server
npx http-server -p 8000

# 使用Live Server (VS Code扩展)
# 右键点击index.html -> Open with Live Server
```

## 项目结构

```
personal-website/
├── index.html          # 主页面
├── styles.css          # 样式文件
├── script.js           # JavaScript功能
├── package.json        # 项目配置
└── README.md          # 项目说明
```

## 自定义内容

### 修改个人信息

1. 编辑 `index.html` 中的以下部分：
   - 导航栏标题
   - 首页个人信息
   - 关于我部分
   - 技能列表
   - 项目展示
   - 联系方式

### 修改样式

1. 编辑 `styles.css` 文件
2. 主要颜色变量：
   - 主色调：`#3498db`
   - 强调色：`#f39c12`
   - 渐变背景：`linear-gradient(135deg, #667eea 0%, #764ba2 100%)`

### 添加功能

1. 编辑 `script.js` 文件
2. 已包含的功能：
   - 移动端导航
   - 平滑滚动
   - 表单验证
   - 动画效果
   - 返回顶部按钮

## 浏览器支持

- Chrome (推荐)
- Firefox
- Safari
- Edge
- 移动端浏览器

## 部署

### GitHub Pages

1. 将代码推送到GitHub仓库
2. 在仓库设置中启用GitHub Pages
3. 选择主分支作为源

### Netlify

1. 连接GitHub仓库
2. 设置构建命令：`npm run build`
3. 设置发布目录：`/`

### Vercel

1. 导入GitHub仓库
2. 自动部署

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！

## 联系方式

- 邮箱：your.email@example.com
- GitHub：@yourusername
- 网站：https://yourwebsite.com

