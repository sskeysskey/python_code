// 保存 WSJ 页面待完成下载的图片下载ID，key 为 tabId
let wsjDownloadsPending = {};

chrome.action.onClicked.addListener(async (tab) => {
  if (
    tab.url.includes("ft.com") ||
    tab.url.includes("bloomberg.com") ||
    tab.url.includes("wsj.com") ||
    tab.url.includes("economist.com") ||
    tab.url.includes("technologyreview.com")
  ) {
    try {
      // 执行文本提取与复制操作
      const [result] = await chrome.scripting.executeScript({
        target: { tabId: tab.id },
        function: extractAndCopy
      });

      if (result.result) {
        // 显示文本复制成功通知
        await chrome.scripting.executeScript({
          target: { tabId: tab.id },
          function: showNotification,
          args: ['已成功复制到剪贴板']
        });
      } else {
        // 显示复制失败通知
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

// 修改后的下载图片消息监听器，增加下载完成跟踪逻辑
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'downloadImage') {
    const tabId = sender.tab ? sender.tab.id : null;
    if (tabId !== null) {
      // 初始化该 tab 的下载队列
      if (!wsjDownloadsPending[tabId]) {
        wsjDownloadsPending[tabId] = [];
      }
    }
    chrome.downloads.download({
      url: request.url,
      filename: request.filename,
      saveAs: false // 直接下载，不显示保存对话框
    }, (downloadId) => {
      if (downloadId && tabId !== null) {
        // 将下载任务ID加入跟踪队列中
        wsjDownloadsPending[tabId].push(downloadId);
      }
    });
  }
});

// 新增监听器：检测下载完成后弹出通知
chrome.downloads.onChanged.addListener((delta) => {
  if (delta.state && delta.state.current === "complete") {
    chrome.downloads.search({ id: delta.id }, (results) => {
      if (results && results.length > 0) {
        const downloadItem = results[0];
        const downloadId = downloadItem.id;
        // 遍历所有 wsj 页面的 tabId
        for (const tabId in wsjDownloadsPending) {
          const index = wsjDownloadsPending[tabId].indexOf(downloadId);
          if (index !== -1) {
            // 移除该下载任务ID
            wsjDownloadsPending[tabId].splice(index, 1);
            // 如果该 tab 下所有图片都下载完成，则弹出通知
            if (wsjDownloadsPending[tabId].length === 0) {
              chrome.scripting.executeScript({
                target: { tabId: parseInt(tabId) },
                function: showNotification,
                args: ['所有图片下载完成']
              });
              // 清理该 tab 对应的数据
              delete wsjDownloadsPending[tabId];
            }
            break;
          }
        }
      }
    });
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
    // 定义主要内容选择器
    const mainSelectors = [
      '.body-content p[class*="media-ui-Paragraph_text"]',
      'p.media-ui-Paragraph_text-SqIsdNjhOtO-',
      'p[class*="media-ui-Paragraph_text"]',
      'p.paywall[data-component="paragraph"]',
      // 更通用的选择器，用于捕获可能的段落
      'p[class*="Paragraph"]',
      'p[class*="paragraph"]'
    ];

    // 需要排除的选择器
    const excludeSelectors = [
      '.UpNext_upNext__C39c6',
      '[data-testid="story-card-small"]',
      '.story-card-small',
      '.styles_moreFromBloomberg_HrR5_',
      '.recirc-box-small-list'
    ];

    let paragraphs = [];

    // 获取主要内容
    mainSelectors.forEach(selector => {
      const elements = document.querySelectorAll(selector);
      if (elements && elements.length > 0) {
        elements.forEach(element => {
          // 检查是否在被排除的区域内
          const isInExcludedArea = excludeSelectors.some(excludeSelector =>
            element.closest(excludeSelector) !== null
          );

          if (!isInExcludedArea) {
            paragraphs.push(element);
          }
        });
      }
    });

    // 提取和清理文本
    textContent = [...new Set(paragraphs)]
      .map(p => {
        let text = p.textContent.trim()
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
        return text &&
          text.length > 10 && // 最小长度要求
          !/^[@•∞]/.test(text) && // 不以特殊字符开头
          !/^\s*$/.test(text) && // 不是纯空白
          !['flex', 'Advertisement'].includes(text) && // 排除特定词语
          !/^[.\s]*$/.test(text) && // 不是纯点号或空白
          !/^Up Next:/.test(text) && // 排除"Up Next"开头的文本
          !/^You are using an/.test(text); // 排除浏览器升级提示
      })
      .join('\n\n');
  }

  else if (window.location.hostname.includes("wsj.com")) {
    const article = document.querySelector('article');

    if (article) {
      // 【1】先提取文本，而不进行图片下载
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

      // 找到第一个 h3 标签的索引，将其之后的段落排除掉
      let h3Index = -1;
      for (let i = 0; i < allParagraphs.length; i++) {
        const prevElement = allParagraphs[i].previousElementSibling;
        if (prevElement && prevElement.matches('h3[data-type="hed"]')) {
          h3Index = i;
          break;
        }
      }

      // 如果找到 h3 标签，只保留之前的段落
      if (h3Index !== -1) {
        allParagraphs = allParagraphs.slice(0, h3Index);
      }
      // 去重后生成最终文本内容
      allParagraphs = [...new Set(allParagraphs)];

      textContent = allParagraphs
        .map(p => {
          // 如果包含 strong 标签则跳过
          if (p.querySelector('strong[data-type="emphasis"]')) {
            return '';
          }

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
            !/^.$/.test(text) &&
            !text.includes("Newsletter Sign-up") &&
            !text.includes("Catch up on the headlines, understand the news and make better decisions, free in your inbox daily. Enjoy a free article in every edition.") &&
            !text.includes("News and analysis of the New York City mayor's case") &&
            !text.includes("Latest news and key analysis, selected by editors") &&
            !text.includes("广告");
        })
        .join('\n\n');

      // 【2】只有当文本提取成功后，再进行图片下载
      if (textContent) {
        const pictures = article.querySelectorAll('picture.css-u314cv');
        pictures.forEach(picture => {
          const img = picture.querySelector('img');
          if (img && img.src && img.alt) {
            // 从 srcset 中获取最高分辨率的图片URL
            let highestResUrl = img.src; // 默认使用 src 作为备选

            if (img.srcset) {
              const srcsetEntries = img.srcset.split(',').map(entry => {
                const [url, width] = entry.trim().split(' ');
                return {
                  url: url.trim(),
                  width: parseInt(width) || 0
                };
              });

              // 找出最大宽度的图片URL
              const highestResSrc = srcsetEntries.reduce((prev, current) => {
                return (current.width > prev.width) ? current : prev;
              }, srcsetEntries[0]);

              if (highestResSrc) {
                highestResUrl = highestResSrc.url;
              }
            }

            // 尝试构建最高分辨率版本的URL
            const baseUrl = highestResUrl.split('?')[0];
            const highResUrl = `${baseUrl}?width=700&size=1.5042117930204573&pixel_ratio=2`;

            chrome.runtime.sendMessage({
              action: 'downloadImage',
              url: highResUrl,
              filename: `${img.alt.replace(/[/\\?%*:|"<>]/g, '-')}.jpg`
            });
          }
        });
      }
    }

    // 如果提取到了有效文本，则复制到剪贴板
    if (textContent) {
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
                // 处理 small 标签，保持大写
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
  // 如果未添加通知相关的样式，则创建一次
  if (!document.getElementById('notification-style')) {
    const style = document.createElement('style');
    style.id = 'notification-style';
    style.textContent = `
      #notification-container {
    position: fixed;
    top: 20px;
      left: 50%;
        transform: translateX(-50%);
        z-index: 2147483647;
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 10px;
      }
      .copy-notification {
        background-color: #4CAF50;
    color: white;
    padding: 12px 24px;
    border-radius: 4px;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
    font-size: 14px;
    }
  `;
    document.head.appendChild(style);
  }

  // 创建通知容器（如果尚未创建）
  let container = document.getElementById('notification-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'notification-container';
    document.body.appendChild(container);
  }

  // 创建新的通知元素
  const notification = document.createElement('div');
  notification.className = 'copy-notification';
  notification.textContent = message;
  container.appendChild(notification);

  // 持续显示7秒后直接移除通知
  setTimeout(() => {
    notification.remove();
    // 如果容器内没有其他通知则移除容器
    if (container.children.length === 0) {
      container.remove();
    }
  }, 7000);
}