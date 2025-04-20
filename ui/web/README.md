# AI Automation Interface Assets

This folder contains all static assets needed for the AI Automation Interface, including CSS styles, JavaScript files, audio files, and images.

## File Structure

```
assets/
├── css/                 # Style sheets
│   ├── main.css         # Main style sheet
│   └── themes/          # Theme styles
│       ├── harmony.css  # Light theme
│       └── night.css    # Dark theme
├── js/                  # JavaScript files
│   ├── main.js          # Main interaction logic
│   ├── animations.js    # UI animation effects
│   └── audio_effects.js # Audio effects control
├── audio/               # Sound effects
│   ├── click.mp3        # Click sound
│   ├── notification.mp3 # Notification sound
│   └── ambient/         # Ambient sounds
│       ├── calm.mp3     # Meditation/relaxation background
│       └── focus.mp3    # Focus work background
└── images/              # Image resources
    ├── icons/           # UI icons
    └── backgrounds/     # Background images
```

## CSS Components

### Main CSS (main.css)

The main stylesheet implements a responsive and accessible UI framework with the following features:

- Responsive grid system supporting mobile, tablet, and desktop layouts
- CSS variables for easy theming
- Base component styles (buttons, cards, forms, tables)
- Utility classes for common styling needs
- Accessibility enhancements (focus states, skip links)

#### Grid System

The grid system uses flexbox with 12 columns:

```html
<div class="container">
  <div class="row">
    <div class="col-12 col-md-6 col-lg-4">Column 1</div>
    <div class="col-12 col-md-6 col-lg-4">Column 2</div>
    <div class="col-12 col-md-6 col-lg-4">Column 3</div>
  </div>
</div>
```

#### Theme Support

The CSS is designed with theming in mind, using CSS variables that can be overridden by theme stylesheets:

```css
:root {
  --primary-color: #3498db;
  --secondary-color: #2ecc71;
  --text-color: #333333;
  /* Additional variables */
}
```

### Themes

#### Harmony Theme (harmony.css)

A light theme with soft, harmonious colors and subtle gradients:

- White background with blue accent colors
- Soft shadows and subtle hover effects
- High contrast for readability

#### Night Theme (night.css)

A dark theme optimized for reduced eye strain and nighttime use:

- Dark background with reduced blue light
- Subtle glow effects and dark-optimized contrast
- Custom scrollbars and focus indicators

## JavaScript Functionality

### Main.js

Handles core interactive functionality:

- Theme switching with system preference detection
- Form validation with error handling
- Storage of user preferences in localStorage
- SPA-like page navigation without refresh

#### Theme Switching

```javascript
// Toggle between light and dark themes
function toggleTheme() {
  document.body.classList.toggle('night-theme');
  document.body.classList.toggle('harmony-theme');
  // Save preference to localStorage
  localStorage.setItem('theme', document.body.classList.contains('night-theme') ? 'night' : 'harmony');
}
```

#### Form Validation

```javascript
// Example form validation
const form = document.querySelector('form');
form.addEventListener('submit', validateForm);
```

### Animations.js

Handles all animation effects and transitions:

- Entry/exit animations for page elements
- Interactive feedback animations
- Modal and toast notifications
- Typing effects for text elements

#### Toast Notifications

```javascript
// Show a toast notification
function showToast(message, type = 'info', duration = 3000) {
  // Implementation details in animations.js
}

// Usage
showToast('Settings saved successfully!', 'success');
```

#### Modal Dialogs

```javascript
// Show a modal dialog
function showModal(title, content, options = {}) {
  // Implementation details in animations.js
}

// Usage
showModal('Confirm Action', 'Are you sure you want to continue?', {
  confirmButton: true,
  cancelButton: true,
  onConfirm: () => processAction()
});
```

### Audio_effects.js

Manages all sound-related functionality:

- UI interaction sounds
- Notification sounds
- Ambient background audio
- Volume control and user preferences

#### Playing Sounds

```javascript
// Play a notification sound
function playNotificationSound() {
  // Implementation details in audio_effects.js
}

// Play an ambient background sound
function playAmbientSound(name) {
  // Implementation details in audio_effects.js
}
```

## Audio Assets

### UI Sounds

- **click.mp3**: Short click sound for buttons and interactions
- **notification.mp3**: Attention-getting notification sound

### Ambient Sounds

- **calm.mp3**: Relaxing background sound for meditation/relaxation features
- **focus.mp3**: Concentration-enhancing background sound for work sessions

## Image Assets

### Icons

SVG icons for UI elements with the following features:
- Clean, minimalist design
- Consistent 24x24 sizing
- Support for theming via CSS
- Accessibility attributes

### Backgrounds

Background images optimized for different screen sizes and themes.

## Usage Examples

### Basic Page Structure

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AI Automation Interface</title>
  <link rel="stylesheet" href="assets/css/main.css">
  <link rel="stylesheet" href="assets/css/themes/harmony.css">
  <link rel="stylesheet" href="assets/css/themes/night.css">
</head>
<body class="harmony-theme">
  <header>
    <nav class="navbar">
      <div class="container">
        <a href="/" class="navbar-brand">AI Automation</a>
        <button class="navbar-toggle" aria-label="Toggle navigation">
          <span></span>
        </button>
        <ul class="navbar-nav">
          <li class="nav-item"><a href="/" class="nav-link active">Dashboard</a></li>
          <li class="nav-item"><a href="/projects" class="nav-link">Projects</a></li>
          <li class="nav-item"><a href="/settings" class="nav-link">Settings</a></li>
        </ul>
        <button id="theme-toggle" aria-label="Toggle theme">🌙</button>
      </div>
    </nav>
  </header>
  
  <main id="main-content" class="container">
    <!-- Page content here -->
  </main>
  
  <footer>
    <div class="container">
      <p>&copy; 2025 AI Automation Interface</p>
    </div>
  </footer>
  
  <script src="assets/js/main.js"></script>
  <script src="assets/js/animations.js"></script>
  <script src="assets/js/audio_effects.js"></script>
</body>
</html>
```

### Theme Toggle Button

```html
<button id="theme-toggle" aria-label="Toggle theme">🌙</button>
```

```javascript
// Initialize theme toggle
document.getElementById('theme-toggle').addEventListener('click', toggleTheme);
```

### Form with Validation

```html
<form id="settings-form">
  <div class="form-group">
    <label for="username">Username</label>
    <input type="text" id="username" class="form-control" required>
  </div>
  
  <div class="form-group">
    <label for="email">Email</label>
    <input type="email" id="email" class="form-control" required>
  </div>
  
  <button type="submit" class="btn btn-primary">Save Settings</button>
</form>
```

### Card Component

```html
<div class="card">
  <h3 class="card-title">Project Name</h3>
  <div class="card-body">
    <p>Project description and details go here.</p>
  </div>
  <div class="card-footer">
    <button class="btn btn-primary">Edit</button>
    <button class="btn btn-outline">Delete</button>
  </div>
</div>
```

## Accessibility Features

- WCAG 2.1 AA 标准合规性
- 键盘导航支持
- 高对比度文本
- 适当的 ARIA 标签
- 跳过导航链接
- 语义化 HTML
- 屏幕阅读器兼容性

## 性能优化

所有资源文件都经过了优化，以确保快速加载和流畅的用户体验：

### CSS 优化

- 压缩的 CSS 文件供生产环境使用
- 使用 CSS 变量减少重复
- 媒体查询优化移动体验

### JavaScript 优化

- 压缩和混淆的 JS 文件供生产环境使用
- 事件委托减少事件监听器数量
- 懒加载非关键功能

### 图像优化

- SVG 图标确保在所有分辨率下清晰
- 响应式图像加载不同大小的图片
- 图像压缩减少文件大小

### 音频优化

- 压缩音频文件减少大小
- 按需加载环境音效
- 音频预缓存避免播放延迟

## 浏览器兼容性

资源已在以下浏览器的最新两个版本中测试：

- Chrome
- Firefox
- Safari
- Edge

## 开发指南

### 添加新主题

要创建新主题，请遵循以下步骤：

1. 在 `assets/css/themes/` 中创建新的 CSS 文件
2. 覆盖基本 CSS 变量以定义颜色和样式
3. 为特定组件添加自定义样式

```css
/* 例：创建新主题 */
body.new-theme-name {
  --primary-color: #your-color;
  --secondary-color: #your-color;
  /* 其他变量覆盖 */
}

/* 特定组件样式 */
body.new-theme-name .card {
  /* 自定义样式 */
}
```

### 创建新图标

所有图标应为 SVG 格式，遵循以下规范：

- 24x24 基础尺寸（viewBox="0 0 24 24"）
- 线条粗细一致（通常为 1.5-2px）
- 使用 CSS 变量引用颜色，允许主题切换
- 包含适当的 ARIA 属性

```html
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" aria-hidden="true">
  <path d="..." fill="currentColor" />
</svg>
```

### 添加新音效

添加新音效时应考虑：

- 文件格式：使用 MP3 格式保持兼容性
- 音量：保持一致的音量水平（避免突然的响声）
- 持续时间：UI 音效保持简短（<0.5s）
- 文件大小：优化压缩以减小文件大小

## 资源引用

在 HTML 中，使用以下模式引用资源：

```html
<!-- CSS 引用 -->
<link rel="stylesheet" href="assets/css/main.css">
<link rel="stylesheet" href="assets/css/themes/harmony.css">

<!-- JavaScript 引用 -->
<script src="assets/js/main.js"></script>
<script src="assets/js/animations.js"></script>
<script src="assets/js/audio_effects.js"></script>

<!-- 图像引用 -->
<img src="assets/images/icons/home.svg" alt="Home">

<!-- 背景图像 -->
<div style="background-image: url('assets/images/backgrounds/pattern.jpg')"></div>
```

## 示例页面

以下是一个完整页面示例，展示了所有组件的集成：

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AI 自动化界面</title>
  <link rel="stylesheet" href="assets/css/main.css">
  <link rel="stylesheet" href="assets/css/themes/harmony.css">
  <link rel="stylesheet" href="assets/css/themes/night.css">
</head>
<body class="harmony-theme">
  <a href="#main-content" class="skip-to-content">跳到主要内容</a>
  
  <header>
    <nav class="navbar">
      <div class="container">
        <a href="/" class="navbar-brand">AI 自动化</a>
        <button class="navbar-toggle" aria-label="切换导航菜单" aria-expanded="false">
          <span></span>
        </button>
        <ul class="navbar-nav">
          <li class="nav-item"><a href="/" class="nav-link active">仪表盘</a></li>
          <li class="nav-item"><a href="/projects" class="nav-link">项目</a></li>
          <li class="nav-item"><a href="/settings" class="nav-link">设置</a></li>
        </ul>
        <button id="theme-toggle" aria-label="切换主题">🌙</button>
      </div>
    </nav>
  </header>
  
  <main id="main-content" class="container">
    <h1>欢迎使用 AI 自动化界面</h1>
    
    <div class="row">
      <div class="col-12 col-md-6 col-lg-4">
        <div class="card">
          <h2 class="card-title">快速入门</h2>
          <div class="card-body">
            <p>开始使用自动化工具来提高工作效率。</p>
            <button class="btn btn-primary">开始</button>
          </div>
        </div>
      </div>
      
      <div class="col-12 col-md-6 col-lg-4">
        <div class="card">
          <h2 class="card-title">进度报告</h2>
          <div class="card-body">
            <p>查看您的自动化任务进度。</p>
            <div class="progress">
              <div class="progress-bar" style="width: 75%" data-progress="75"></div>
            </div>
          </div>
        </div>
      </div>
      
      <div class="col-12 col-md-6 col-lg-4">
        <div class="card">
          <h2 class="card-title">设置</h2>
          <div class="card-body">
            <p>配置您的自动化环境。</p>
            <button class="btn btn-outline">设置</button>
          </div>
        </div>
      </div>
    </div>
    
    <section class="section-animate mt-5">
      <h2>表单示例</h2>
      <form id="settings-form">
        <div class="form-group">
          <label for="username">用户名</label>
          <input type="text" id="username" class="form-control" required>
        </div>
        
        <div class="form-group">
          <label for="email">电子邮件</label>
          <input type="email" id="email" class="form-control" required>
        </div>
        
        <div class="form-group">
          <label>首选项</label>
          <div class="form-check">
            <input type="checkbox" id="pref-email" class="form-check-input">
            <label for="pref-email" class="form-check-label">接收电子邮件通知</label>
          </div>
          <div class="form-check">
            <input type="checkbox" id="pref-sound" class="form-check-input">
            <label for="pref-sound" class="form-check-label">启用声音效果</label>
          </div>
        </div>
        
        <button type="submit" class="btn btn-primary">保存设置</button>
      </form>
    </section>
  </main>
  
  <footer class="mt-5">
    <div class="container">
      <p class="text-center">&copy; 2025 AI 自动化界面</p>
    </div>
  </footer>
  
  <script src="assets/js/main.js"></script>
  <script src="assets/js/animations.js"></script>
  <script src="assets/js/audio_effects.js"></script>
  <script>
    // 初始化组件
    document.addEventListener('DOMContentLoaded', function() {
      // 添加音频反馈
      audioEffects.addAudioFeedback();
      
      // 示例：显示一条通知
      setTimeout(() => {
        uiAnimations.showToast('欢迎回来!', 'info', 3000);
      }, 2000);
    });
  </script>
</body>
</html>
```

## 贡献指南

贡献新资源时，请遵循以下指南：

1. 遵循现有的命名约定
2. 优化资源以减小文件大小
3. 为所有资源提供文档
4. 确保资源在所有支持的浏览器中正常工作
5. 保持设计语言的一致性

## 许可证信息

所有自定义资源文件在 [合适的许可证] 下提供。
第三方资源可能有其自己的许可要求，详情请参阅各自的许可证文件。

## 联系方式

如有任何问题或建议，请联系：[联系方式]