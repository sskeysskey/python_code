document.addEventListener('DOMContentLoaded', () => {
    const loadingElement = document.getElementById('loading');
    const noVideosElement = document.getElementById('no-videos');
    const videosContainerElement = document.getElementById('videos-container');
    const videoListElement = document.getElementById('video-list');
    const videoCountElement = document.getElementById('video-count');
    const scanButton = document.getElementById('scan-btn');

    // 获取当前标签页中找到的视频
    function getVideos() {
        chrome.runtime.sendMessage({ type: 'GET_VIDEOS' }, (response) => {
            const videos = response.urls || [];

            // 更新UI
            if (videos.length === 0) {
                loadingElement.classList.add('hidden');
                noVideosElement.classList.remove('hidden');
                videosContainerElement.classList.add('hidden');
            } else {
                loadingElement.classList.add('hidden');
                noVideosElement.classList.add('hidden');
                videosContainerElement.classList.remove('hidden');

                // 更新视频计数
                videoCountElement.textContent = videos.length;

                // 清空视频列表
                videoListElement.innerHTML = '';

                // 添加视频到列表
                videos.forEach((url, index) => {
                    const listItem = document.createElement('li');
                    listItem.className = 'video-item';

                    const videoInfo = document.createElement('div');
                    videoInfo.className = 'video-info';
                    videoInfo.textContent = `视频 ${index + 1}`;

                    const downloadButton = document.createElement('button');
                    downloadButton.className = 'download-btn';
                    downloadButton.textContent = '下载';
                    downloadButton.addEventListener('click', () => {
                        chrome.runtime.sendMessage({
                            type: 'DOWNLOAD_VIDEO',
                            url: url
                        });
                    });

                    listItem.appendChild(videoInfo);
                    listItem.appendChild(downloadButton);
                    videoListElement.appendChild(listItem);
                });
            }
        });
    }

    // 初始化扫描
    function scanForVideos() {
        loadingElement.classList.remove('hidden');
        noVideosElement.classList.add('hidden');
        videosContainerElement.classList.add('hidden');

        // 告诉内容脚本扫描视频
        chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
            if (tabs[0] && tabs[0].url.includes('snapchat.com')) {
                chrome.tabs.sendMessage(tabs[0].id, { type: 'SCAN_VIDEOS' }, () => {
                    // 延迟一点时间以等待视频扫描完成
                    setTimeout(getVideos, 1000);
                });
            } else {
                loadingElement.classList.add('hidden');
                noVideosElement.classList.remove('hidden');
                videosContainerElement.classList.add('hidden');
            }
        });
    }

    // 监听重新扫描按钮点击
    scanButton.addEventListener('click', scanForVideos);

    // 监听来自后台脚本的更新消息
    chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
        if (message.type === 'UPDATE_VIDEOS') {
            getVideos();
        }
        return true;
    });

    // 初始化
    scanForVideos();
});