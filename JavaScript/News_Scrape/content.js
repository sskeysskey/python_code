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
function scrapeWSJ(shouldDownload = true) {
    const now = new Date();
    const currentDatetime = `${now.getFullYear()}_${String(now.getMonth() + 1).padStart(2, '0')}_${String(now.getDate()).padStart(2, '0')}_${String(now.getHours()).padStart(2, '0')}`;
    const newRows = [];
    const hostname = window.location.hostname;

    // 添加新的选择器 css-g4pnb7
    const titleElements = document.querySelectorAll('h3.css-fsvegl a, article h2 a, .WSJTheme--headline--7VCzo7Ay a, .css-g4pnb7, .css-2pp34t');

    titleElements.forEach(titleElement => {
        const href = titleElement.href;

        // 跳过包含 livecoverage 或 buyside 的链接
        if (!href || href.toLowerCase().includes('livecoverage') || href.toLowerCase().includes('wsj.com/buyside') || href.toLowerCase().includes('wsj.com/video')) {
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

    // 只有当 shouldDownload 为 true 且有内容时才下载
    if (shouldDownload && newRows.length > 0) {
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

    return newRows.length;
}

// 主抓取函数
function scrapeAndDownload() {
    const hostname = window.location.hostname;

    if (hostname.includes('bloomberg.com')) {
        scrapeBloomberg();
    } else if (hostname.includes('wsj.com')) {
        // WSJ的处理在专门的函数中进行
        handleWSJScraping();
    }
}

// 专门处理WSJ的抓取
function handleWSJScraping() {
    // // 第一次抓取但不下载
    // scrapeWSJ(false);

    // // 2秒后进行第二次抓取并下载
    // setTimeout(() => {
    //     console.log('执行WSJ的第二次抓取...');
    //     scrapeWSJ(true);
    // }, 1000);
}

// 根据网站使用不同的事件监听方式
const hostname = window.location.hostname;

if (hostname.includes('bloomberg.com')) {
    // Bloomberg 使用原来的 load 事件
    window.addEventListener('load', () => {
        console.log('Bloomberg Scraper loaded');
        scrapeBloomberg();
    });
} else if (hostname.includes('wsj.com')) {
    // WSJ 使用 DOMContentLoaded 事件
    document.addEventListener('DOMContentLoaded', () => {
        console.log('WSJ Scraper loaded');
        handleWSJScraping();
    });

    // 对于动态加载的内容，添加 MutationObserver 来监测DOM变化
    function throttle(func, limit) {
        let inThrottle;
        return function () {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        }
    }

    // 在观察到DOM变化后，仅执行第二次抓取并下载
    const throttledScrape = throttle(() => {
        console.log('检测到WSJ页面变化，执行额外抓取...');
        scrapeWSJ(true);
    }, 5000);  // 至少间隔5秒

    // 等待初始抓取完成后再设置观察器
    setTimeout(() => {
        const observer = new MutationObserver(throttledScrape);

        // 配置 observer
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });

        // 2分钟后断开观察器以避免长时间消耗资源
        setTimeout(() => {
            observer.disconnect();
        }, 2 * 60 * 1000);
    }, 3000);
}