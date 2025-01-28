chrome.action.onClicked.addListener(async (tab) => {
  if (tab.url.includes("ft.com") || tab.url.includes("bloomberg.com") ||
    tab.url.includes("wsj.com") || tab.url.includes("economist.com") ||
    tab.url.includes("technologyreview.com")) {
    try {
      // 执行提取与复制操作
      const [result] = await chrome.scripting.executeScript({
        target: { tabId: tab.id },
        function: extractAndCopy
      });

      if (result.result) {
        // 显示成功通知
        await chrome.scripting.executeScript({
          target: { tabId: tab.id },
          function: showNotification,
          args: ['已成功复制到剪贴板']
        });
      } else {
        // 显示失败通知
        await chrome.scripting.executeScript({
          target: { tabId: tab.id },
          function: showNotification,
          args: ['复制失败，未找到内容']
        });
      }
    } catch (err) {
      console.error('Script execution failed:', err);
      // 显示错误通知
      await chrome.scripting.executeScript({
        target: { tabId: tab.id },
        function: showNotification,
        args: ['发生错误，请重试']
      });
    }
  }
});

function extractAndCopy() {
  let textContent = '';

  if (window.location.hostname.includes("ft.com")) {
    // FT.com 的内容提取逻辑
    const articleBody = document.getElementById('article-body');

    if (articleBody) {
      const paragraphs = articleBody.getElementsByTagName('p');
      textContent = Array.from(paragraphs)
        .map(p => p.textContent.trim())
        .filter(text => text && text !== '@' && text !== '•' && text !== '».' && text.length > 1)
        .join('\n\n');
    }
  }

  else if (window.location.hostname.includes("bloomberg.com")) {
    // Bloomberg.com 的内容提取逻辑
    let paragraphs = [];

    // 定义多个可能的选择器组合
    const selectors = [
      // 原有的选择器
      '.body-content p[class*="media-ui-Paragraph_text"]',
      // 新页面的选择器
      'p.copy-width',
      // 其他可能的选择器
      'main p',
      'article p',
      '.dvz-content p',
      // 更通用的选择器，用于捕获可能的段落
      'p[class*="Paragraph"]',
      'p[class*="paragraph"]',
      'p[class*="copy"]'
    ];

    // 尝试所有选择器
    for (const selector of selectors) {
      const elements = document.querySelectorAll(selector);
      if (elements && elements.length > 0) {
        paragraphs = [...paragraphs, ...Array.from(elements)];
      }
    }

    // 去重并清理内容
    textContent = [...new Set(paragraphs)]
      .map(p => {
        let text = p.textContent.trim();

        // 增强的文本清理
        text = text
          .replace(/<!--[\s\S]*?-->/g, '') // 移除HTML注释
          .replace(/[•∞@]/g, '') // 移除特殊字符
          .replace(/\s+/g, ' ') // 规范化空白
          .replace(/&nbsp;/g, ' ') // 处理HTML空格
          .replace(/==\s*\$\d+/g, '') // 移除调试标记
          .replace(/<![-—]{2,}>/g, '') // 移除HTML注释标记
          .replace(/<\/?[^>]+(>|$)/g, '') // 移除HTML标签
          .trim();

        return text;
      })
      .filter(text => {
        // 增强过滤条件
        return text &&
          text.length > 10 && // 增加最小长度要求
          !/^[@•∞]/.test(text) && // 不以特殊字符开头
          !/^\s*$/.test(text) && // 不是纯空白
          !['flex', 'Advertisement'].includes(text) && // 排除特定词语
          !/^[.\s]*$/.test(text) && // 不是纯点号或空格
          !/^You are using an/.test(text) && // 排除浏览器升级提示
          text !== '@' &&
          text !== '•' &&
          text !== '∞';
      })
      .join('\n\n');
  }

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

  else if (window.location.hostname.includes("economist.com")) {
    const article = document.querySelector('[data-test-id="Article"]');
    if (article) {
      const paragraphs = article.querySelectorAll('p[data-component="paragraph"]');

      textContent = Array.from(paragraphs)
        .map(p => {
          // 递归获取所有文本内容的函数
          function getAllText(node) {
            let text = '';

            // 处理所有子节点
            Array.from(node.childNodes).forEach(child => {
              if (child.nodeType === Node.TEXT_NODE) {
                text += child.textContent;
              } else if (child.nodeType === Node.ELEMENT_NODE) {
                // 特殊处理大写字母开头
                if (child.tagName === 'SPAN' && child.getAttribute('data-caps') === 'initial') {
                  text += child.textContent;
                }
                // 处理small标签，保持大写
                else if (child.tagName === 'SMALL') {
                  text += child.textContent;
                }
                // 处理链接和其他元素
                else if (child.tagName === 'A' || child.children.length > 0) {
                  text += getAllText(child);
                }
                else {
                  text += child.textContent;
                }
              }
            });
            return text;
          }

          // 获取并清理文本
          let text = getAllText(p)
            .replace(/\s+/g, ' ') // 规范化空白
            .replace(/[•∞@]/g, '') // 移除特殊字符
            .replace(/&nbsp;/g, ' ') // 处理HTML空格
            .trim();

          return text;
        })
        .filter(text => {
          return text &&
            text.length > 5 &&
            !['@', '•', '∞', 'flex'].includes(text) &&
            !/^\s*$/.test(text) &&
            !/^[.\s]*$/.test(text) &&
            !/^By\s/.test(text);
        })
        .join('\n\n');
    }
  }

  else if (window.location.hostname.includes("technologyreview.com")) {
    console.log('Debug: Detected Technology Review website'); // 调试日志

    // 更新 Technology Review 的内容提取逻辑
    const contentBody = document.querySelector('#content--body');
    console.log('Debug: Content body found:', !!contentBody); // 调试日志

    if (contentBody) {
      // 尝试多个可能的选择器
      let paragraphs = [];

      // 选择器列表
      const selectors = [
        // 新的选择器
        'div[class*="gutenbergContent"] p',
        '.html_0 p, .html_2 p, .html_8 p',
        '.contentBody_content--42a60b56e419a26d9c3638a9dab52f55 p',
        // 备用选择器
        '#content--body p',
        'article p',
        '.contentBody_wrapper p'
      ];

      // 依次尝试每个选择器
      for (const selector of selectors) {
        const elements = contentBody.querySelectorAll(selector);
        if (elements && elements.length > 0) {
          paragraphs = elements;
          console.log(`Debug: Found ${elements.length} paragraphs using selector: ${selector}`);
          break;
        }
      }

      // 如果还是没找到，使用最基础的选择器
      if (!paragraphs.length) {
        paragraphs = contentBody.getElementsByTagName('p');
        console.log('Debug: Using basic p tag selector, found:', paragraphs.length);
      }

      textContent = Array.from(paragraphs)
        .map(p => {
          let text = p.textContent.trim();

          // 增强的文本清理
          text = text
            .replace(/\s+/g, ' ') // 规范化空白
            .replace(/[\u200B-\u200D\uFEFF]/g, '') // 移除零宽字符
            .replace(/&nbsp;/g, ' ') // 处理HTML空格
            .replace(/<!--[\s\S]*?-->/g, '') // 移除HTML注释
            .replace(/\[.*?\]/g, '') // 移除方括号内容
            .trim();

          return text;
        })
        .filter(text => {
          // 增强的过滤条件
          const invalidTexts = [
            'flex',
            'Skip to Content',
            'You need to enable JavaScript',
            '@',
            '•',
            '∞',
            '.',
            'Advertisement'
          ];

          return text &&
            text.length > 10 && // 增加最小长度要求
            !invalidTexts.includes(text) &&
            !/^\s*$/.test(text) &&
            !/^Update:/.test(text) &&
            !/^Related Story/.test(text) &&
            !/^[\.•@∞]+$/.test(text);
        })
        .join('\n\n');

      // 调试信息
      console.log('Debug: Final extracted text length:', textContent.length);
      if (!textContent) {
        console.log('Debug: No content extracted after filtering');
      } else {
        console.log('Debug: Content successfully extracted');
        // 输出前100个字符用于验证
        console.log('Debug: First 100 chars:', textContent.substring(0, 100));
      }
    }
  }

  if (textContent) {
    // 创建一个隐藏的 textarea 元素以复制文本
    const textarea = document.createElement('textarea');
    textarea.style.position = 'fixed';
    textarea.style.opacity = '0';
    textarea.value = textContent;
    document.body.appendChild(textarea);
    textarea.select();

    try {
      document.execCommand('copy');
      return true;
    } catch (err) {
      console.error('复制失败:', err);
      return false;
    } finally {
      document.body.removeChild(textarea);
    }
  }
  return false;
}

function showNotification(message) {
  // 创建通知样式
  const style = document.createElement('style');
  style.textContent = `
    .copy-notification {
    position: fixed;
    top: 20px;
      left: 50%;
      transform: translateX(-50%) translateY(-20px);
    background-color: #4CAF50;  /* 相同的绿色，使用十六进制表示 */
    color: white;
    padding: 12px 24px;
    border-radius: 4px;
      z-index: 2147483647;
    box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
    font-size: 14px;
    opacity: 0;
    transition: all 0.3s ease;
    }
  `;
  document.head.appendChild(style);

  // 移除可能存在的旧通知
  const existingNotification = document.querySelector('.copy-notification');
  if (existingNotification) {
    existingNotification.remove();
  }

  // 创建新通知
  const notification = document.createElement('div');
  notification.className = 'copy-notification';
  notification.textContent = message;
  document.body.appendChild(notification);

  // 触发动画
  requestAnimationFrame(() => {
    notification.style.opacity = '1';
    notification.style.transform = 'translateX(-50%) translateY(0)';
  });

  // 7秒后淡出
  setTimeout(() => {
    notification.style.opacity = '0';
    notification.style.transform = 'translateX(-50%) translateY(-20px)';
    setTimeout(() => {
      notification.remove();
      style.remove();
    }, 300);
  }, 7000);
}