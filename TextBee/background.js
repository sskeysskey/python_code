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
      // 文本提取逻辑保持不变
      const paragraphs = articleBody.getElementsByTagName('p');
      textContent = Array.from(paragraphs)
        .map(p => p.textContent.trim())
        .filter(text => text && text !== '@' && text !== '•' && text !== '».' && text.length > 1)
        .join('\n\n');

      // 如果成功提取到文本，则处理图片下载
      if (textContent) {
        // 查找所有图片容器
        const figures = document.querySelectorAll('figure.n-content-image');

        figures.forEach(figure => {
          const picture = figure.querySelector('picture');
          if (picture) {
            // 获取最高分辨率的图片URL
            const desktopSource = picture.querySelector('source[media="(min-width: 700px)"]');
            const img = picture.querySelector('img');

            if (desktopSource && desktopSource.srcset) {
              // 从srcset中提取最高分辨率的URL
              const srcsetUrls = desktopSource.srcset.split(',')
                .map(src => src.trim().split(' ')[0])
                .filter(url => url);

              if (srcsetUrls.length > 0) {
                // 使用最后一个URL（通常是最高分辨率的）
                const highResUrl = srcsetUrls[srcsetUrls.length - 1];

                // 生成文件名
                let filename;
                if (img && img.alt) {
                  // 使用图片alt文本作为文件名
                  filename = `ft-${img.alt.replace(/[/\\?%*:|"<>]/g, '-')}.jpg`;
                } else {
                  // 如果没有alt文本，使用时间戳
                  const timestamp = new Date().getTime();
                  filename = `ft-image-${timestamp}.jpg`;
                }

                // 确保文件名不会太长
                if (filename.length > 100) {
                  filename = filename.substring(0, 96) + '.jpg';
                }

                // 发送下载消息到background script
                chrome.runtime.sendMessage({
                  action: 'downloadImage',
                  url: highResUrl,
                  filename: filename
                });
              }
            } else if (img && img.src) {
              // 如果没有source标签，使用img的src
              const filename = img.alt
                ? `ft-${img.alt.replace(/[/\\?%*:|"<>]/g, '-')}.jpg`
                : `ft-image-${new Date().getTime()}.jpg`;

              chrome.runtime.sendMessage({
                action: 'downloadImage',
                url: img.src,
                filename: filename
              });
            }
          }
        });
      }
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

    // 如果提取到了有效文本，则进行图片下载
    if (textContent) {
      // 查找所有类型的图片容器
      const articleImages = document.querySelectorAll('figure[data-component="article-image"]');

      articleImages.forEach(figure => {
        const img = figure.querySelector('img.ui-image.high-res-img');
        if (img) {
          let highestResUrl = img.src; // 默认使用src

          // 如果有srcset，解析并找出最高分辨率的图片
          if (img.srcset) {
            const srcsetEntries = img.srcset.split(',')
              .map(entry => {
                // 提取URL和宽度
                const parts = entry.trim().split(' ');
                const url = parts[0].trim();
                // 从类似 "1200w" 的字符串中提取数字
                const width = parseInt(parts[parts.length - 1]) || 0;
                return { url, width };
              })
              .filter(entry => entry.width > 0) // 只保留有效的宽度值
              .sort((a, b) => b.width - a.width); // 按宽度降序排序

            // 使用最高分辨率的URL
            if (srcsetEntries.length > 0) {
              highestResUrl = srcsetEntries[0].url;
            }
          }

          // 清理URL（移除多余的空格和换行）
          highestResUrl = highestResUrl.replace(/\s+/g, '');

          // 获取文件扩展名
          const extension = highestResUrl.toLowerCase().includes('.png') ? 'png' : 'webp';

          // 生成文件名
          let filename;
          if (img.alt) {
            // 使用alt文本作为文件名
            filename = `bloomberg-${img.alt.replace(/[/\\?%*:|"<>]/g, '-')}.${extension}`;
          } else {
            // 如果没有alt文本，使用时间戳
            const timestamp = new Date().getTime();
            filename = `bloomberg-image-${timestamp}.${extension}`;
          }

          // 确保文件名不会太长
          if (filename.length > 100) {
            filename = filename.substring(0, 96) + '.' + extension;
          }

          // 发送下载消息到background script
          chrome.runtime.sendMessage({
            action: 'downloadImage',
            url: highestResUrl,
            filename: filename
          });
        }
      });
    }
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
          // 过滤掉带有特定class的段落
          if (
            p.querySelector('strong[data-type="emphasis"]') ||
            p.className.includes('g-pstyle') ||  // 添加这个条件
            p.closest('.ai2html_export') ||      // 添加这个条件
            p.closest('[data-block="dynamic-inset"]') // 添加这个条件
          ) {
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

      // 如果成功提取到文本，则处理图片下载
      if (textContent) {
        // 查找所有图片，但排除特定区域的图片
        const figures = Array.from(article.querySelectorAll('figure.css-3mn275'))
          .filter(figure => {
            // 检查父元素，排除相关文章区域的图片
            return !figure.closest('[data-optimizely="related-articles-section"]') && // 排除相关文章区域
              !figure.closest('[data-tracking-id="content-well-chapter-list"]') && // 排除章节列表
              !figure.closest('.css-1qaigru') && // 排除水平布局区域
              !figure.closest('.css-12lyffs'); // 排除推荐文章卡片
          });

        figures.forEach(figure => {
          const img = figure.querySelector('img');
          if (img) {
            // 检查图片格式
            let fileExtension = 'jpg';
            const srcUrl = img.src || '';
            if (srcUrl.includes('format=auto')) {
              // 从原始URL中提取实际文件扩展名
              const originalPath = srcUrl.split('/').pop().split('_')[1];
              if (originalPath) {
                const match = originalPath.match(/\.(jpg|jpeg|png|gif|webp)$/i);
                if (match) {
                  fileExtension = match[1].toLowerCase();
                }
              }
            }

            // 构建最高质量的图片URL
            // 移除现有的width参数，使用1424作为最大宽度
            const baseUrl = srcUrl.split('/content-assets/')[0] + '/content-assets/';
            const imagePath = srcUrl.split('/content-assets/')[1].split('?')[0];
            const highResUrl = `${baseUrl}${imagePath}?width=1424&quality=80&format=auto`;

            // 生成文件名
            let filename;
            if (img.alt && img.alt.trim()) {
              // 使用图片alt文本作为文件名，替换非法字符
              filename = `economist-${img.alt.replace(/[/\\?%*:|"<>]/g, '-')}.${fileExtension}`;
            } else {
              // 如果没有alt文本，使用时间戳
              const timestamp = new Date().getTime();
              filename = `economist-image-${timestamp}.${fileExtension}`;
            }

            // 确保文件名不会太长
            if (filename.length > 100) {
              filename = filename.substring(0, 96) + '.' + fileExtension;
            }

            // 发送下载消息到background script
            chrome.runtime.sendMessage({
              action: 'downloadImage',
              url: highResUrl,
              filename: filename
            });
          }
        });
      }
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

      if (textContent) {
        // 查找所有文章图片
        const images = document.querySelectorAll('img[srcset]');

        images.forEach(img => {
          if (img && img.srcset) {
            // 提取基础文件名
            const baseFileName = "250218_globalelectricity";

            // 直接构造最高质量的图片URL
            const highResUrl = `https://wp.technologyreview.com/wp-content/uploads/2025/02/${baseFileName}.jpg?fit=2252,1266`;

            // 生成文件名
            let filename;
            if (img.alt && img.alt.trim()) {
              filename = `technologyreview-${img.alt.replace(/[/\\?%*:|"<>]/g, '-')}`;
            } else {
              const timestamp = new Date().getTime();
              filename = `technologyreview-image-${timestamp}`;
            }

            // 确保文件名不会太长且以.jpg结尾
            if (filename.length > 90) {
              filename = filename.substring(0, 90);
            }
            if (!filename.toLowerCase().endsWith('.jpg')) {
              filename += '.jpg';
            }

            // 输出调试信息
            console.log('Attempting to download:', {
              url: highResUrl,
              filename: filename
            });

            // 发送下载消息
            chrome.runtime.sendMessage({
              action: 'downloadImage',
              url: highResUrl,
              filename: filename
            });
          }
        });
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