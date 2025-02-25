// ——————————————————————————————————————————————————————————————
//   // 检查多种可能的尺寸来源
//   const width = img.width || img.naturalWidth ||
//     parseInt(img.getAttribute('width')) ||
//     parseInt(window.getComputedStyle(img).width) || 0;

//   const height = img.height || img.naturalHeight ||
//     parseInt(img.getAttribute('height')) ||
//     parseInt(window.getComputedStyle(img).height) || 0;

//   // 检查图片的实际显示尺寸
//   const rect = img.getBoundingClientRect();
//   const displayWidth = rect.width;
//   const displayHeight = rect.height;

//   // 检查data属性中可能包含的尺寸信息
//   const dataWidth = parseInt(img.dataset.width || '0');
//   const dataHeight = parseInt(img.dataset.height || '0');

//   // 综合判断图片尺寸
//   const isTooSmall = (
//     // 检查实际尺寸
//     (width > 0 && height > 0 && (width < 150 || height < 150)) ||
//     // 检查显示尺寸
//     (displayWidth > 0 && displayHeight > 0 && (displayWidth < 150 || displayHeight < 150)) ||
//     // 检查data属性尺寸
//     (dataWidth > 0 && dataHeight > 0 && (dataWidth < 150 || dataHeight < 150))
//   );

//   // 检查图片的样式类名，排除可能的小图标
//   const hasIconClass = img.className.toLowerCase().includes('icon') ||
//     img.className.toLowerCase().includes('avatar') ||
//     img.className.toLowerCase().includes('thumb');

//   // 检查父元素是否暗示这是一个小图标
//   const parentIndicatesIcon = img.parentElement && (
//     img.parentElement.className.toLowerCase().includes('icon') ||
//     img.parentElement.className.toLowerCase().includes('avatar') ||
//     img.parentElement.className.toLowerCase().includes('thumbnail')
//   );

//   return !isTooSmall && !hasIconClass && !parentIndicatesIcon;
// });

// ——————————————————————————————————————————————————————————————
const creditSpan = picture.closest('[data-type="image"]')?.querySelector('.css-7jz429-Credit');
const altText = creditSpan ? creditSpan.textContent : (img.alt || 'wsj_image');

// 发送下载请求
chrome.runtime.sendMessage({
    action: 'downloadImage',
    url: finalUrl,
    filename: `${altText.replace(/[/\\?*:|"<>]/g, '-')}.jpg`
});

// ——————————————————————————————————————————————————————————————
else if (window.location.hostname.includes("wsj.com")) {
    // WSJ.com 的内容提取逻辑
    const article = document.querySelector('article');
    if (article) {
        // 定义可能的段落选择器
        const possibleSelectors = [
            // 第一种样式
            'p[class*="emoc1hq1"][class*="css-1jdwmf4-StyledNewsKitParagraph"][font-size="17"]',
            // 第二种样式
            'p[class*="css-k3zb61-Paragraph"]',
            // 备用选择器
            'p[data-type="paragraph"]',
            '.paywall p[data-type="paragraph"]',
            'article p[data-type="paragraph"]',
            // 添加新的选择器以提高兼容性
            'p[class*="Paragraph"]',
            '.paywall p'
        ];

        // 合并所有找到的段落
        let allParagraphs = [];
        possibleSelectors.forEach(selector => {
            const paragraphs = article.querySelectorAll(selector);
            allParagraphs = [...allParagraphs, ...Array.from(paragraphs)];
        });

        // 去重
        allParagraphs = [...new Set(allParagraphs)];

        textContent = allParagraphs
            .map(p => {
                // 获取段落的纯文本内容
                let text = p.textContent.trim();

                // 处理特殊字符和HTML注释
                text = text
                    .replace(/<!--[\s\S]*?-->/g, '') // 移除HTML注释
                    .replace(/[•∞@]/g, '') // 移除特殊字符
                    .replace(/\s+/g, ' ') // 规范化空白
                    .replace(/&nbsp;/g, ' ') // 处理HTML空格
                    .replace(/≤\/p>/g, '') // 处理HTML标签碎片
                    .replace(/\[.*?\]/g, '') // 处理方括号内容
                    .trim();

                return text;
            })
            .filter(text => {
                // 增强过滤条件
                return text &&
                    text.length > 1 &&
                    !['@', '•', '∞', 'flex'].includes(text) &&
                    !/^\s*$/.test(text) &&
                    !/^Advertisement$/i.test(text) &&
                    !/^.$/.test(text); // 过滤单个字符
            })
            .join('\n\n');
    }
}

else if (window.location.hostname.includes("wsj.com")) {
    const article = document.querySelector('article');
    let content = [];

    if (article) {
        // 提取图片
        const pictures = article.querySelectorAll('picture.css-u314cv');
        pictures.forEach(picture => {
            const img = picture.querySelector('img');
            if (img) {
                const imageInfo = {
                    type: 'image',
                    alt: img.alt || '',
                    src: img.src || ''
                };
                content.push(imageInfo);
            }
        });

        // 提取文字段落 (原有的段落提取逻辑)
        const possibleSelectors = [
            'p[class*="emoc1hq1"][class*="css-1jdwmf4-StyledNewsKitParagraph"][font-size="17"]',
            'p[class*="css-k3zb61-Paragraph"]',
            'p[data-type="paragraph"]',
            '.paywall p[data-type="paragraph"]',
            'article p[data-type="paragraph"]',
            'p[class*="Paragraph"]',
            '.paywall p'
        ];

        let allParagraphs = [];
        possibleSelectors.forEach(selector => {
            const paragraphs = article.querySelectorAll(selector);
            allParagraphs = [...allParagraphs, ...Array.from(paragraphs)];
        });

        allParagraphs = [...new Set(allParagraphs)];

        const textParagraphs = allParagraphs
            .map(p => {
                let text = p.textContent.trim()
                    .replace(/<!--[\s\S]*?-->/g, '')
                    .replace(/[•∞@]/g, '')
                    .replace(/\s+/g, ' ')
                    .replace(/&nbsp;/g, ' ')
                    .replace(/≤\/p>/g, '')
                    .replace(/\[.*?\]/g, '')
                    .trim();

                return text;
            })
            .filter(text => {
                return text &&
                    text.length > 1 &&
                    !['@', '•', '∞', 'flex'].includes(text) &&
                    !/^\s*$/.test(text) &&
                    !/^Advertisement$/i.test(text) &&
                    !/^.$/.test(text);
            });

        // 合并图片和文字内容
        textContent = content.map(item => {
            if (item.type === 'image') {
                return `描述: ${item.alt}\n链接: ${item.src}\n`;
            }
            return item;
        }).join('\n\n');

        // 添加文字内容
        textContent += '\n\n' + textParagraphs.join('\n\n');
    }
}
// ——————————————————————————————————————————————————————————————

// 如果没有找到内容，尝试备用方案
if (!textContent || textContent.length < 50) {
    console.log('使用备用提取方案');
    // 尝试获取所有段落内容
    const backupParagraphs = article.getElementsByTagName('p');
    textContent = Array.from(backupParagraphs)
        .map(p => p.textContent.trim())
        .filter(text => {
            return text &&
                text.length > 1 &&
                !['@', '•', '∞', 'flex'].includes(text) &&
                !/^\s*$/.test(text);
        })
        .join('\n\n');
}

// 添加调试信息
console.log('找到段落数量:', allParagraphs.length);
console.log('提取的文本长度:', textContent?.length);