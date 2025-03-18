// 用于在页面中检测视频的内容脚本
let foundVideos = new Set();
let observerActive = false;

// 创建一个MutationObserver来监视DOM变化
const observer = new MutationObserver(() => {
    detectVideos();
});

// 检测页面上的所有视频
function detectVideos() {
    // 获取所有视频元素
    const videos = document.querySelectorAll('video');
    let newVideosFound = false;

    videos.forEach(video => {
        // 检查视频源
        if (video.src && !foundVideos.has(video.src) && video.src.startsWith('blob:')) {
            foundVideos.add(video.src);
            newVideosFound = true;

            // 尝试提取真实视频URL
            fetchBlobUrl(video.src);
        }

        // 检查source元素
        const sources = video.querySelectorAll('source');
        sources.forEach(source => {
            if (source.src && !foundVideos.has(source.src)) {
                foundVideos.add(source.src);
                newVideosFound = true;
            }
        });
    });

    if (newVideosFound) {
        updateVideoList();
    }
}

// 尝试提取blob URL的实际内容
async function fetchBlobUrl(blobUrl) {
    try {
        // 获取blob内容
        const response = await fetch(blobUrl);
        const blob = await response.blob();

        // 创建临时URL以供下载
        const url = URL.createObjectURL(blob);

        // 添加到找到的视频中
        if (!foundVideos.has(url)) {
            foundVideos.add(url);
            updateVideoList();
        }
    } catch (error) {
        console.error('提取blob内容时出错:', error);
    }
}

// 将找到的视频发送到后台脚本
function updateVideoList() {
    chrome.runtime.sendMessage({
        type: 'FOUND_VIDEOS',
        urls: Array.from(foundVideos)
    });
}

// 用于监听网络请求中的媒体文件
function setupRequestCapture() {
    // 由于 manifest v3 的限制，我们需要使用内容脚本来捕获请求
    const originalFetch = window.fetch;
    window.fetch = async function (...args) {
        const response = await originalFetch.apply(this, args);

        // 克隆响应以便我们可以使用它
        const clone = response.clone();

        try {
            const contentType = response.headers.get('content-type') || '';
            const url = response.url;

            // 如果是视频或音频内容
            if (contentType.includes('video/') ||
                contentType.includes('audio/') ||
                url.includes('.mp4') || url.includes('.m3u8')) {

                if (!foundVideos.has(url)) {
                    foundVideos.add(url);
                    updateVideoList();
                }
            }
        } catch (e) {
            console.error('分析响应时出错:', e);
        }

        return response;
    };

    // 覆盖XMLHttpRequest
    const originalXhrOpen = XMLHttpRequest.prototype.open;
    XMLHttpRequest.prototype.open = function (method, url) {
        this.addEventListener('load', function () {
            const contentType = this.getResponseHeader('content-type') || '';

            if (contentType.includes('video/') ||
                contentType.includes('audio/') ||
                url.includes('.mp4') || url.includes('.m3u8')) {

                if (!foundVideos.has(url)) {
                    foundVideos.add(url);
                    updateVideoList();
                }
            }
        });

        return originalXhrOpen.apply(this, arguments);
    };
}

// 启动扩展功能
function init() {
    // 启动观察器
    if (!observerActive) {
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
        observerActive = true;
    }

    // 设置网络请求捕获
    setupRequestCapture();

    // 初始检测
    detectVideos();
}

// 在页面加载完成后初始化
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}

// 监听消息
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === 'SCAN_VIDEOS') {
        detectVideos();
        sendResponse({ success: true });
    }
    return true;
});