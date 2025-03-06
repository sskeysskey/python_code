// 处理标题是否有效的函数
function isValidTitle(titleText) {
    const invalidPhrases = [
        'Illustration:', '/Bloomberg', 'Getty Images', '/AP Photo', '/AP', 'Photos:',
        'Photo illustration', 'Source:', '/AFP', 'NurPhoto', 'SOurce:', 'WireImage',
        'Listen (', 'Podcast:'
    ];

    if (invalidPhrases.some(phrase => titleText.includes(phrase))) {
        return false;
    }

    if ((titleText.includes('Listen') || titleText.includes('Watch')) &&
        titleText.includes('(') && titleText.includes(')')) {
        titleText = titleText.split(')')[1].trim();
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

// 主抓取函数
function scrapeBloombergNews() {
    const currentDatetime = new Date().toISOString().slice(0, 13).replace(/-/g, '_').replace('T', '_');
    const links = document.querySelectorAll("a[href*='/2025']");
    const newRows = [];

    links.forEach(link => {
        const href = link.href;
        let titleText = link.textContent.trim();

        if (titleText.startsWith("Newsletter: ")) {
            titleText = titleText.substring(11);
        }

        // 跳过视频链接
        if (href.includes('/videos/2025')) {
            console.log(`Skipped video link: ${href}`);
            return;
        }

        console.log(`Processing element: Href: ${href}, Text: ${titleText}`);

        if (isValidTitle(titleText) && href) {
            newRows.push([currentDatetime, titleText, href]);
            console.log(`Added new row: ${titleText}`);
        } else {
            console.log(`Skipped: ${titleText}`);
        }
    });

    return newRows;
}

// 监听来自popup.js的消息
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "scrapeNews") {
        const results = scrapeBloombergNews();
        sendResponse({ success: true, data: results });
    }
    return true; // 保持消息通道开放，以便异步响应
});