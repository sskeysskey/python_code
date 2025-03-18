// 用于在页面中检测视频的内容脚本
let foundVideos = [];  // 改为数组以存储视频URL和相关用户名
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
        if (video.src && video.src.startsWith('blob:')) {
            // 检查这个视频是否已经在列表中
            const existingVideo = foundVideos.find(v => v.url === video.src);
            if (!existingVideo) {
                // 尝试找到相关的用户名称
                const videoInfo = {
                    url: video.src,
                    title: "未知视频",
                    username: ""
                };

                // 尝试获取与视频相关的用户名
                // 首先查找包含视频的父元素
                let videoContainer = video;
                let maxSearchDepth = 10; // 防止无限循环
                let depth = 0;

                while (videoContainer && depth < maxSearchDepth) {
                    // 向上查找父元素，直到找到一个可能包含用户信息的元素
                    videoContainer = videoContainer.parentElement;
                    depth++;

                    // 如果找到了父容器，在其中查找用户名
                    if (videoContainer) {
                        // 查找用户名元素，根据你提供的HTML，通常在VonaH nonIntl类的元素内
                        const userNameElement = videoContainer.querySelector('.VonaH.nonIntl h3');
                        if (userNameElement && userNameElement.textContent) {
                            videoInfo.username = userNameElement.textContent.trim();
                            videoInfo.title = `${videoInfo.username}的视频`;
                            break;
                        }

                        // 如果找不到h3，尝试查找其他可能包含用户名的元素
                        const altUserNameElement = videoContainer.querySelector('a.gtry');
                        if (altUserNameElement) {
                            const username = altUserNameElement.getAttribute('href').split('/').pop();
                            if (username) {
                                videoInfo.username = username;
                                videoInfo.title = `${username}的视频`;
                                break;
                            }
                        }
                    }
                }

                foundVideos.push(videoInfo);
                newVideosFound = true;

                // 尝试提取真实视频URL
                fetchBlobUrl(video.src, videoInfo);
            }
        }

        // 检查source元素
        const sources = video.querySelectorAll('source');
        sources.forEach(source => {
            if (source.src) {
                const existingVideo = foundVideos.find(v => v.url === source.src);
                if (!existingVideo) {
                    // 类似逻辑来获取用户名
                    const videoInfo = {
                        url: source.src,
                        title: "未知视频",
                        username: ""
                    };

                    // ...同上的用户名检测代码
                    foundVideos.push(videoInfo);
                    newVideosFound = true;
                }
            }
        });
    });

    if (newVideosFound) {
        updateVideoList();
    }
}

// 尝试提取blob URL的实际内容
async function fetchBlobUrl(blobUrl, videoInfo) {
    try {
        // 获取blob内容
        const response = await fetch(blobUrl);
        const blob = await response.blob();

        // 创建临时URL以供下载
        const url = URL.createObjectURL(blob);

        // 添加到找到的视频中
        const existingVideo = foundVideos.find(v => v.url === blobUrl);
        if (existingVideo) {
            // 更新URL为可下载的URL
            existingVideo.downloadUrl = url;
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
        videos: foundVideos
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

                const existingVideo = foundVideos.find(v => v.url === url);
                if (!existingVideo) {
                    // 尝试确定与此URL相关的上下文
                    const videoInfo = {
                        url: url,
                        title: `视频 (${url.split('/').pop()})`,
                        username: ""
                    };

                    foundVideos.push(videoInfo);
                    updateVideoList();
                }
            }
        } catch (e) {
            console.error('分析响应时出错:', e);
        }

        return response;
    };

    // 覆盖XMLHttpRequest，类似上面的逻辑
    const originalXhrOpen = XMLHttpRequest.prototype.open;
    XMLHttpRequest.prototype.open = function (method, url) {
        this.addEventListener('load', function () {
            const contentType = this.getResponseHeader('content-type') || '';

            if (contentType.includes('video/') ||
                contentType.includes('audio/') ||
                url.includes('.mp4') || url.includes('.m3u8')) {

                const existingVideo = foundVideos.find(v => v.url === url);
                if (!existingVideo) {
                    const videoInfo = {
                        url: url,
                        title: `视频 (${url.split('/').pop()})`,
                        username: ""
                    };

                    foundVideos.push(videoInfo);
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