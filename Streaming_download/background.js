// 用于处理视频下载的后台脚本
let videoUrls = [];

// 监听来自内容脚本的消息
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === 'FOUND_VIDEOS') {
        videoUrls = message.urls;
        // 更新扩展图标上的数字标志
        chrome.action.setBadgeText({ text: videoUrls.length.toString() });
        chrome.action.setBadgeBackgroundColor({ color: '#FF0000' });

        // 通知popup更新
        chrome.runtime.sendMessage({ type: 'UPDATE_VIDEOS', urls: videoUrls });
        sendResponse({ success: true });
    } else if (message.type === 'GET_VIDEOS') {
        sendResponse({ urls: videoUrls });
    } else if (message.type === 'DOWNLOAD_VIDEO') {
        // 下载视频
        chrome.downloads.download({
            url: message.url,
            filename: `snapchat_video_${Date.now()}.mp4`,
            saveAs: true
        });
        sendResponse({ success: true });
    }
    return true;
});

// 当标签页更新时重置视频列表
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
    if (changeInfo.status === 'complete' && tab.url.includes('snapchat.com')) {
        videoUrls = [];
        chrome.action.setBadgeText({ text: '' });
    }
});