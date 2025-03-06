// 存储抓取结果
let scrapedData = [];

// 初始化
document.addEventListener('DOMContentLoaded', function () {
    document.getElementById('scrapeBtn').addEventListener('click', scrapeNews);
    document.getElementById('downloadBtn').addEventListener('click', downloadHTML);

    // 从存储中恢复数据
    chrome.storage.local.get(['bloombergNews'], function (result) {
        if (result.bloombergNews) {
            scrapedData = result.bloombergNews;
            updateStatus(`已有 ${scrapedData.length} 条新闻数据`);
        }
    });
});

// 抓取新闻
function scrapeNews() {
    updateStatus('正在抓取...');

    chrome.tabs.query({ active: true, currentWindow: true }, function (tabs) {
        chrome.tabs.sendMessage(tabs[0].id, { action: "scrapeNews" }, function (response) {
            if (response && response.success) {
                scrapedData = response.data;
                chrome.storage.local.set({ bloombergNews: scrapedData });
                updateStatus(`成功抓取 ${scrapedData.length} 条新闻`);
            } else {
                updateStatus('抓取失败，请检查是否在Bloomberg网站');
            }
        });
    });
}

// 生成HTML内容
function generateHTML() {
    let html = `<html><body><table border='1'>\n<tr><th>Date</th><th>Title</th></tr>\n`;

    scrapedData.forEach(row => {
        const clickableTitle = `<a href='${row[2]}' target='_blank'>${row[1]}</a>`;
        html += `<tr><td>${row[0]}</td><td>${clickableTitle}</td></tr>\n`;
    });

    html += `</table></body></html>`;
    return html;
}

// 下载HTML文件
function downloadHTML() {
    if (scrapedData.length === 0) {
        updateStatus('没有数据可下载');
        return;
    }

    const html = generateHTML();
    const blob = new Blob([html], { type: 'text/html' });
    const url = URL.createObjectURL(blob);

    chrome.downloads.download({
        url: url,
        filename: 'bloomberg.html'
        // 移除 saveAs: true 参数或设置为 false
    }, function (downloadId) {
        updateStatus('文件下载成功');
    });
}

// 更新状态信息
function updateStatus(message) {
    document.getElementById('status').textContent = message;
}