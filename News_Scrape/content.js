// 处理标题是否有效的函数
function isValidTitle(titleText) {
    const invalidPhrases = [
        'Illustration:', '/Bloomberg', 'Getty Images', '/AP Photo', '/AP', 'Photos:',
        'Photo illustration', 'Source:', '/AFP', 'NurPhoto', 'SOurce:', 'WireImage',
        'Podcast:'
    ];

    // 过滤掉仅包含 "LIVE" 的标题
    if (titleText.trim() === "LIVE") {
        return false;
    }

    // 过滤掉以 "Listen" 开头的标题
    if (titleText.trim().startsWith("Listen")) {
        return false;
    }

    if (invalidPhrases.some(phrase => titleText.includes(phrase))) {
        return false;
    }

    return titleText && !isTimeFormat(titleText);
}

// 判断是否为时间格式
function isTimeFormat(text) {
    if ((text.length === 4 || text.length === 5) && text.includes(':')) {
        const parts = text.split(':');
        return parts.every(part => !isNaN(parseInt(part)));
    }
    return false;
}

// 生成HTML内容
function generateHTML(data, source) {
    let html = `
<html>
<body>
  <table border='1'>
    <tr><th>Date</th><th>Title</th></tr>
`;

    data.forEach(row => {
        const clickableTitle = `<a href='${row[2]}' target='_blank'>${row[1]}</a>`;
        html += `<tr><td>${row[0]}</td><td>${clickableTitle}</td></tr>\n`;
    });

    html += `</table></body></html>`;
    return html;
}

// Bloomberg 抓取函数
function scrapeBloomberg() {
    const now = new Date();
    const currentDatetime = `${now.getFullYear()}_${String(now.getMonth() + 1).padStart(2, '0')}_${String(now.getDate()).padStart(2, '0')}_${String(now.getHours()).padStart(2, '0')}`;
    const links = document.querySelectorAll("a[href*='/2025']");
    const newRows = [];

    links.forEach(link => {
        const href = link.href;
        let titleText = link.textContent.trim();

        if (titleText.startsWith("Newsletter: ")) {
            titleText = titleText.substring(11);
        }

        if (href.includes('/videos/2025')) {
            return;
        }

        if (isValidTitle(titleText) && href) {
            newRows.push([currentDatetime, titleText, href]);
        }
    });

    if (newRows.length > 0) {
        const html = generateHTML(newRows, 'Bloomberg');
        const blob = new Blob([html], { type: 'text/html' });
        const url = URL.createObjectURL(blob);
        const timestamp = now.toLocaleString('zh-CN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: false
        }).replace(/[/: ]/g, '_');

        chrome.runtime.sendMessage({
            action: "downloadHTML",
            url: url,
            filename: `bloomberg_${timestamp}.html`
        });
    }
}

// WSJ 抓取函数
function scrapeWSJ() {
    const now = new Date();
    const currentDatetime = `${now.getFullYear()}_${String(now.getMonth() + 1).padStart(2, '0')}_${String(now.getDate()).padStart(2, '0')}_${String(now.getHours()).padStart(2, '0')}`;
    const newRows = [];
    const hostname = window.location.hostname;

    // 添加新的选择器 css-g4pnb7
    const titleElements = document.querySelectorAll('h3.css-fsvegl a, article h2 a, .WSJTheme--headline--7VCzo7Ay a, .css-g4pnb7, .css-2pp34t');

    titleElements.forEach(titleElement => {
        const href = titleElement.href;

        // 跳过包含 livecoverage 的链接
        if (!href || href.toLowerCase().includes('livecoverage')) {
            return;
        }

        // 检查链接域名，只保留 wsj.com 的链接
        try {
            const url = new URL(href);
            if (!url.hostname.includes('wsj.com')) {
                return;
            }
        } catch (e) {
            // 如果 URL 解析失败，跳过这个链接
            return;
        }

        let titleText = titleElement.innerText.trim();

        // 移除阅读时间标记
        titleText = titleText.replace(/\d+ min read/g, '').trim();

        if (titleText && href) {
            newRows.push([currentDatetime, titleText, href]);
        }
    });

    if (newRows.length > 0) {
        const html = generateHTML(newRows, 'WSJ');
        const blob = new Blob([html], { type: 'text/html' });
        const url = URL.createObjectURL(blob);
        const timestamp = now.toLocaleString('zh-CN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: false
        }).replace(/[/: ]/g, '_');

        // 根据域名决定文件名前缀
        const prefix = hostname.includes('cn.wsj.com') ? 'cnwsj_' : 'wsj_';

        chrome.runtime.sendMessage({
            action: "downloadHTML",
            url: url,
            filename: `${prefix}${timestamp}.html`
        });
    }
}

// 主抓取函数
function scrapeAndDownload() {
    const hostname = window.location.hostname;

    if (hostname.includes('bloomberg.com')) {
        scrapeBloomberg();
    } else if (hostname.includes('wsj.com')) {
        scrapeWSJ();
    }
}

// 当页面加载完成后自动执行抓取
window.addEventListener('load', () => {
    console.log('News Scraper content script loaded for: ' + window.location.hostname);
    scrapeAndDownload();
});