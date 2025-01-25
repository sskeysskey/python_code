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