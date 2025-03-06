// 当扩展安装或更新时初始化
chrome.runtime.onInstalled.addListener(function () {
    console.log('Bloomberg News Scraper 已安装');

    // 初始化存储
    chrome.storage.local.set({ bloombergNews: [] });
});