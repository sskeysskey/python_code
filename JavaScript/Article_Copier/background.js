// 保存 WSJ 页面待完成下载的图片下载ID，key 为 tabId
let DownloadsPending = {};

// 点击扩展图标时触发
chrome.action.onClicked.addListener(async (tab) => {
  if (
    tab.url.includes("ft.com") ||
    tab.url.includes("bloomberg.com") ||
    tab.url.includes("wsj.com") ||
    tab.url.includes("economist.com") ||
    tab.url.includes("technologyreview.com") ||
    tab.url.includes("reuters.com") ||
    tab.url.includes("nytimes.com") ||
    tab.url.includes("washingtonpost.com")
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
      // 初始化该 tab 的数据结构
      if (!DownloadsPending[tabId]) {
        DownloadsPending[tabId] = {
          downloads: [],
          hasStartedImageProcess: true
        };
      }
    }
    chrome.downloads.download({
      url: request.url,
      filename: request.filename,
      saveAs: false // 直接下载，不显示保存对话框
    }, (downloadId) => {
      if (downloadId && tabId !== null) {
        // 将下载任务ID加入跟踪队列中
        DownloadsPending[tabId].downloads.push(downloadId);
      }
    });
  } else if (request.action === 'noImages') {
    // 处理无图片的情况
    const tabId = sender.tab ? sender.tab.id : null;
    if (tabId !== null) {
      chrome.scripting.executeScript({
        target: { tabId: tabId },
        function: showNotification,
        args: ['没有找到可下载的图片']
      });
    }
  }
});

// 监听下载完成后弹出通知
chrome.downloads.onChanged.addListener((delta) => {
  if (delta.state && delta.state.current === "complete") {
    chrome.downloads.search({ id: delta.id }, (results) => {
      if (results && results.length > 0) {
        const downloadItem = results[0];
        const downloadId = downloadItem.id;
        // 遍历所有页面的 tabId
        for (const tabId in DownloadsPending) {
          const tabData = DownloadsPending[tabId];
          const index = tabData.downloads.indexOf(downloadId);
          if (index !== -1) {
            // 移除该下载任务ID
            tabData.downloads.splice(index, 1);
            // 如果该 tab 下所有图片都下载完成，则弹出通知
            if (tabData.downloads.length === 0) {
              chrome.scripting.executeScript({
                target: { tabId: parseInt(tabId) },
                function: showNotification,
                args: ['所有图片下载完成']
              });
              // 清理该 tab 对应的数据
              delete DownloadsPending[tabId];
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

  // 处理 FT.com
  if (window.location.hostname.includes("ft.com")) {
    // FT.com 的内容提取逻辑
    const articleBody = document.getElementById('article-body');

    if (articleBody) {
      // 改进的文本提取逻辑
      const paragraphs = articleBody.getElementsByTagName('p');
      textContent = Array.from(paragraphs)
        .filter(p => {
          // 获取段落的纯文本内容
          const text = p.textContent.trim();

          // 排除条件：
          // 1. 空段落或只包含特殊字符
          if (!text || text === '@' || text === '•' || text === '».' || text.length <= 1) {
            return false;
          }

          // 2. 包含作者信息的段落
          if (text.includes('is the author of') || text.toLowerCase().includes('follow ft weekend')) {
            return false;
          }

          // 4. 包含编辑说明的段落
          if (text.toLowerCase().includes('change has been made') ||
            text.toLowerCase().includes('story was originally published')) {
            return false;
          }

          // 5. 包含社交媒体链接的段落
          if (text.toLowerCase().includes('follow') &&
            (text.includes('instagram') || text.includes('twitter'))) {
            return false;
          }

          // 6. 排除包含订阅信息的段落
          if (text.toLowerCase().includes('subscribe') || text.toLowerCase().includes('newsletter')) {
            return false;
          }

          // 7. 检查段落是否主要由em标签组成
          const emTags = p.getElementsByTagName('em');
          if (emTags.length > 0 && emTags[0].textContent.length > text.length / 2) {
            return false;
          }

          // 8. 检查是否包含大量链接
          const links = p.getElementsByTagName('a');
          if (links.length > 2) {
            return false;
          }

          // 通过所有检查，保留这个段落
          return true;
        })
        .map(p => p.textContent.trim())
        .join('\n\n');

      if (textContent) {
        // 收集所有需要处理的图片容器
        const imageContainers = [
          ...document.querySelectorAll('figure.n-content-image'),
          ...document.querySelectorAll('figure.n-content-picture'),
          ...document.querySelectorAll('figure.o-topper_visual'),
          ...document.querySelectorAll('.main-image')
        ];

        // 创建Set来存储已处理的URL和文件名
        const processedUrls = new Set();
        const processedFilenames = new Set();

        if (imageContainers.length === 0) {
          chrome.runtime.sendMessage({ action: 'noImages' });
        } else {
          imageContainers.forEach((container, index) => {
            // 首先尝试获取图片描述
            let imageDescription = '';

            // 尝试获取可能包含描述的元素
            const possibleDescriptionElements = [
              container.querySelector('figcaption'), // 尝试figcaption
              container.querySelector('.n-content-picture__caption'), // 特定的caption类
              container.querySelector('.article__image-caption'), // 另一个可能的caption类
              container.closest('figure')?.querySelector('.o-topper__visual-caption'), // 顶部图片的caption
              // 如果有其他可能包含描述的元素，可以继续添加
            ];

            // 遍历所有可能的描述元素
            for (const element of possibleDescriptionElements) {
              if (element && element.textContent.trim()) {
                imageDescription = element.textContent
                  .replace(/©[^]*/g, '') // 移除版权信息
                  .trim();
                break;
              }
            }

            // 处理picture元素
            const picture = container.querySelector('picture');
            if (picture) {
              // 尝试获取所有可能的图片源
              const sources = picture.querySelectorAll('source');
              const img = picture.querySelector('img');

              let highResUrl = '';

              // 获取最高分辨率的图片URL
              if (sources.length > 0) {
                // 遍历所有source标签找到最高分辨率的图片
                sources.forEach(source => {
                  const srcset = source.srcset;
                  if (srcset) {
                    const urls = srcset.split(',')
                      .map(src => src.trim().split(' ')[0])
                      .filter(url => url);

                    if (urls.length > 0) {
                      // 使用最后一个URL（通常是最高分辨率的）
                      const possibleUrl = urls[urls.length - 1];
                      if (possibleUrl.length > highResUrl.length) {
                        highResUrl = possibleUrl;
                      }
                    }
                  }
                });
              }

              // 如果source中没找到，使用img标签的src
              if (!highResUrl && img && img.src) {
                highResUrl = img.src;
              }

              // 检查URL是否已经处理过
              if (highResUrl && !processedUrls.has(highResUrl)) {
                processedUrls.add(highResUrl);

                let filename;
                if (imageDescription) {
                  // 使用找到的描述作为文件名
                  const cleanedDescription = imageDescription
                    .replace(/[/\\?%*:|"<>]/g, '-')
                    .replace(/\s+/g, ' ')
                    .trim();

                  filename = `${cleanedDescription}.jpg`;

                  if (filename.length > 200) {
                    filename = filename.substring(0, 196) + '.jpg';
                  }
                } else if (img && img.alt) {
                  // 如果没有找到描述，退回到使用alt文本
                  const cleanedAlt = img.alt
                    .replace(/[/\\?%*:|"<>]/g, '-')
                    .replace(/\s+/g, ' ')
                    .trim();

                  filename = `${cleanedAlt}.jpg`;

                  // 如果文件名超过200个字符，截取前196个字符
                  if (filename.length > 200) {
                    // 保留前196个字符，然后加上.jpg
                    filename = filename.substring(0, 196) + '.jpg';
                  }
                } else {
                  // 如果既没有描述也没有alt文本，使用时间戳
                  const timestamp = new Date().getTime();
                  filename = `ft-image-${timestamp}-${index}.jpg`;
                }

                // 检查文件名是否已经使用过
                if (!processedFilenames.has(filename)) {
                  processedFilenames.add(filename);
                  chrome.runtime.sendMessage({
                    action: 'downloadImage',
                    url: highResUrl,
                    filename: filename
                  });
                }
              }
            } else {
              // 处理单独的img标签
              const img = container.querySelector('img');
              if (img && img.src && !processedUrls.has(img.src)) {
                processedUrls.add(img.src);

                let filename;
                if (imageDescription) {
                  const cleanedDescription = imageDescription
                    .replace(/[/\\?%*:|"<>]/g, '-')
                    .replace(/\s+/g, ' ')
                    .trim();

                  filename = `${cleanedDescription}.jpg`;

                  if (filename.length > 200) {
                    filename = filename.substring(0, 196) + '.jpg';
                  }
                } else if (img.alt) {
                  // 对单独img标签的alt文本进行同样的处理
                  const cleanedAlt = img.alt
                    .replace(/[/\\?%*:|"<>]/g, '-')
                    .replace(/\s+/g, ' ')
                    .trim();

                  filename = `${cleanedAlt}.jpg`;

                  if (filename.length > 200) {
                    filename = filename.substring(0, 196) + '.jpg';
                  }
                } else {
                  filename = `ft-image-${new Date().getTime()}-${index}.jpg`;
                }

                // 检查文件名是否已经使用过
                if (!processedFilenames.has(filename)) {
                  processedFilenames.add(filename);
                  chrome.runtime.sendMessage({
                    action: 'downloadImage',
                    url: img.src,
                    filename: filename
                  });
                }
              }
            }
          });
        }
      }
    }
  }

  // 处理 bloomberg.com
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
          .replace(/<![---]{2,}>/g, '') // 移除HTML注释标记
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
          !/^[.\s]*$/.test(text) && // 不是纯点号或空格
          !/^Up Next:/.test(text) && // 排除"Up Next"开头的文本
          !/^You are using an/.test(text); // 排除浏览器升级提示
      })
      .join('\n\n');

    // 如果提取到了有效文本，则进行图片下载
    if (textContent) {
      // 查找所有类型的图片容器
      const articleImages = document.querySelectorAll('figure[data-component="article-image"]');

      // 检查是否找到了符合条件的图片
      let foundValidImages = false;

      // 用于存储已处理的图片URL
      const processedUrls = new Set();

      if (articleImages && articleImages.length > 0) {
        articleImages.forEach(figure => {
          const img = figure.querySelector('img.ui-image.high-res-img');
          if (img) {
            foundValidImages = true;
            // 获取图片描述文本 - 新增部分
            let caption = '';
            // 查找figcaption元素
            const figcaption = figure.querySelector('figcaption');
            if (figcaption) {
              // 尝试获取所有可能包含描述的元素
              const captionSpans = figcaption.querySelectorAll('span');
              if (captionSpans && captionSpans.length > 0) {
                // 合并所有span的文本内容
                caption = Array.from(captionSpans)
                  .map(span => span.textContent.trim())
                  .filter(text => text) // 过滤空文本
                  .join(' ');
              } else {
                // 如果没有span，直接获取figcaption的文本
                caption = figcaption.textContent.trim();
              }
            }

            // 图片处理代码
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

            // 检查URL是否已经处理过
            if (!processedUrls.has(highestResUrl)) {
              processedUrls.add(highestResUrl);
              foundValidImages = true;

              // 获取文件扩展名
              const extension = highestResUrl.toLowerCase().includes('.png') ? 'png' : 'webp';

              // 生成文件名
              let filename;
              if (caption) {
                let cleanedCaption = caption
                  .replace(/&nbsp;/g, ' ')
                  // 移除 Photograph- 及其后的内容
                  .replace(/Photograph[\s\S]*$/i, '')
                  // 移除 Photographer- 及其后的内容
                  .replace(/Photographer[\s\S]*$/i, '');

                // 一次性移除 Source- / Source: / Source— 等及其后面的所有内容
                cleanedCaption = cleanedCaption
                  .replace(/\s*(?:Source[-:–—]?)\s*.*$/i, '')
                  .trim();

                filename = `${cleanedCaption.replace(/[/\\?%*:|"<>]/g, '-')}.${extension}`;
              }
              else if (img.alt) {
                let cleanedAlt = img.alt.replace(/&nbsp;/g, ' ')
                  .replace(/Photographer[\s\S]*$/i, '');

                cleanedAlt = cleanedAlt
                  .replace(/\s*(?:Source[-:–—]?)\s*.*$/i, '')
                  .trim();

                filename = `${cleanedAlt.replace(/[/\\?%*:|"<>]/g, '-')}.${extension}`;
              } else {
                // 如果既没有alt也没有caption，使用时间戳
                const timestamp = new Date().getTime();
                filename = `bloomberg-image-${timestamp}.${extension}`;
              }

              // 确保文件名不会太长
              if (filename.length > 200) {
                filename = filename.substring(0, 196) + '.' + extension;
              }

              // 发送下载消息到background script
              chrome.runtime.sendMessage({
                action: 'downloadImage',
                url: highestResUrl,
                filename: filename
              });
            }
          }
        });
      }

      // 在处理完所有图片后，如果没有找到有效图片，则发送noImages消息
      if (!foundValidImages) {
        chrome.runtime.sendMessage({ action: 'noImages' });
      }
    } else {
      // 如果没有提取到有效文本，也应该发送noImages消息
      chrome.runtime.sendMessage({ action: 'noImages' });
    }
  }

  // 处理 wsj.com
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
        // 查找"Show Conversation"元素
        const showConversationElement = document.querySelector('.css-1nc85ca-Show0rHideCommentsSpan');

        // 扩展图片查找范围
        let allImages = [
          ...Array.from(article.querySelectorAll('picture.css-u314cv img')), // 原有的选择器
          ...Array.from(article.querySelectorAll('.origami-item img')), // 新增：origami布局中的图片
          ...Array.from(article.querySelectorAll('[data-type="inset"] img')), // 新增：inset中的图片
          ...Array.from(article.querySelectorAll('figure img')) // 新增：figure中的图片
        ];

        // 如果找到"Show Conversation"元素，则过滤掉其后的图片
        if (showConversationElement) {
          allImages = allImages.filter(img => {
            // 判断图片是否在"Show Conversation"元素之前
            // 使用compareDocumentPosition进行DOM位置比较
            const position = showConversationElement.compareDocumentPosition(img);
            // 如果图片在showConversationElement之后，返回false
            return !(position & Node.DOCUMENT_POSITION_FOLLOWING);
          });
        }

        // 继续进行剩余过滤
        allImages = allImages.filter(img => {
          const imgSrc = img.src || '';

          // 排除SVG和小图标
          if (imgSrc.toLowerCase().endsWith('.svg') ||
            imgSrc.includes('/icons/') ||
            imgSrc.includes('/icons') ||
            imgSrc.includes('/social') ||
            imgSrc.includes('/ui/') ||
            imgSrc.includes('/ui') ||
            img.closest('button, .share-button, .toolbar')) {
            return false;
          }

          // 使用尺寸信息（如果可用）
          const imgWidth = img.width || img.naturalWidth || 0;
          const imgHeight = img.height || img.naturalHeight || 0;
          if (imgWidth > 0 && imgHeight > 0 && (imgWidth < 150 || imgHeight < 150)) {
            return false;
          }

          return true;
        });

        if (allImages.length === 0) {
          chrome.runtime.sendMessage({ action: 'noImages' });
        } else {
          // 用于跟踪已处理的图片URL
          const processedUrls = new Set();

          allImages.forEach(img => {
            if (img) {
              // 清理和标准化srcset字符串
              let highestResUrl = img.src; // 默认使用src

              if (img.srcset) {
                // 清理srcset字符串，移除多余的空格和换行符
                const cleanSrcset = img.srcset.replace(/\n/g, ' ').replace(/\s+/g, ' ').trim();

                // 解析srcset
                const srcsetEntries = cleanSrcset.split(',').map(entry => {
                  const [url, width] = entry.trim().split(/\s+/);
                  // 从width字符串中提取数字
                  const widthNum = parseInt(width?.replace(/[^\d]/g, '') || '0');
                  return {
                    url: url.trim(),
                    width: widthNum
                  };
                });

                // 找出最大宽度的图片URL
                const highestResSrc = srcsetEntries.reduce((prev, current) => {
                  return (current.width > prev.width) ? current : prev;
                }, srcsetEntries[0]);

                if (highestResSrc && highestResSrc.url) {
                  highestResUrl = highestResSrc.url;
                }
              }

              // 获取基础URL（移除查询参数）
              const baseUrl = highestResUrl.split('?')[0];
              const finalUrl = `${baseUrl}?width=700&size=1.2610340479192939&pixel_ratio=2`;

              // 检查是否已处理过该图片
              if (!processedUrls.has(baseUrl)) {
                // 将基础URL添加到已处理集合中
                processedUrls.add(baseUrl);

                // 获取图片描述
                let altText = '';

                // 尝试多种方式获取图片描述
                const origamiCaption = img.closest('.origami-wrapper')?.querySelector('.origami-caption');

                // 新增：如果图片在 <figure> 内，提取其邻近的 <figcaption> 内指定的 caption
                const figureEl = img.closest('figure');
                let captionSpan;
                if (figureEl) {
                  const figcaptionEl = figureEl.nextElementSibling;
                  if (figcaptionEl && figcaptionEl.tagName.toLowerCase() === 'figcaption') {
                    // 获取包含正确描述的 <span>
                    captionSpan = figcaptionEl.querySelector('.css-426zcb-CaptionSpan');
                  }
                }

                // 原代码中查找 credit 作为备用
                const creditSpan = img.closest('[data-type="image"]')?.querySelector('.css-7jz429-Credit');

                if (origamiCaption) {
                  altText = origamiCaption.textContent;
                } else if (captionSpan) {
                  // 优先采用 <figcaption> 里的 caption 内容
                  altText = captionSpan.textContent;
                } else if (creditSpan) {
                  altText = creditSpan.textContent;
                } else {
                  altText = img.alt || 'wsj_image';
                }

                // 文件名处理函数
                const processFileName = (text) => {
                  // 移除或替换特殊字符
                  text = text.replace(/[/\\?%*:|"<>]/g, '-')
                    .replace(/\s+/g, ' ')
                    .trim();

                  // 如果文本超过250个字符，在最接近的单词边界处截断
                  if (text.length > 200) {
                    text = text.substr(0, 196).split(' ').slice(0, -1).join(' ');
                  }

                  return `${text}.jpg`;
                };

                // 只有未处理过的图片才发送下载请求
                chrome.runtime.sendMessage({
                  action: 'downloadImage',
                  url: finalUrl,
                  filename: processFileName(altText)
                });
              }
            }
          });
        }
      }
    }
  }

  // 处理 economist.com
  else if (window.location.hostname.includes("economist.com")) {
    // 首先尝试获取原有的文章结构
    let article = document.querySelector('[data-test-id="Article"]');
    let paragraphs;

    if (article) {
      // 原有网页结构的处理
      paragraphs = article.querySelectorAll('p[data-component="paragraph"]');
    } else {
      // 新网页结构的处理 - 修改这部分以匹配新结构
      article = document.querySelector('.article-text') || document.body; // 如果找不到.article-text则使用body
      if (article) {
        paragraphs = document.querySelectorAll('.article-text body-text, body-text.svelte-16dgy1v');
      }
    }

    if (paragraphs && paragraphs.length > 0) {
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
                // 处理斜体
                else if (child.tagName === 'I') {
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
            return !figure.closest('[data-optimizely="onward-articles-component"]') && // 排除相关文章组件
              !figure.closest('[data-optimizely="related-articles-section"]') && // 排除相关文章区域
              !figure.closest('[data-tracking-id="content-well-chapter-list"]') && // 排除章节列表
              !figure.closest('.css-1qaigru') && // 排除水平布局区域
              !figure.closest('.css-12lyffs') && // 排除推荐文章卡片
              !figure.closest('.css-1xfkcl4'); // 排除onward-articles区域
          });

        if (figures.length === 0) {
          chrome.runtime.sendMessage({ action: 'noImages' });
        } else {
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

              // 优先获取figcaption中的span标签内容作为描述
              let imageDescription = '';
              const figcaptionSpan = figure.querySelector('figcaption span.css-1st60ou');
              if (figcaptionSpan && figcaptionSpan.textContent.trim()) {
                imageDescription = figcaptionSpan.textContent.trim();
              } else if (img.alt && img.alt.trim()) {
                imageDescription = img.alt.trim();
              }

              // 生成文件名
              let filename;
              const now = new Date();
              const timestamp = `${now.getHours()}${now.getMinutes()}${now.getSeconds()}`;

              if (imageDescription) {
                // 使用图片描述作为文件名,替换非法字符,并加上时间戳
                filename = `${imageDescription.replace(/[/\\?%*:|"<>]/g, '-')}.${fileExtension}`;
              } else {
                // 如果没有描述,使用image加时间戳
                filename = `economist-image-${timestamp}.${fileExtension}`;
              }

              // 确保文件名不会太长
              if (filename.length > 200) {
                filename = filename.substring(0, 196) + '.' + fileExtension;
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
  }

  // 处理 technologyreview.com
  else if (window.location.hostname.includes("technologyreview.com")) {

    // 更新 Technology Review 的内容提取逻辑
    const contentBody = document.querySelector('#content--body');

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
        // 简化图片查找逻辑
        const images = contentBody.querySelectorAll('img');

        if (images.length === 0) {
          chrome.runtime.sendMessage({ action: 'noImages' });
        } else {
          images.forEach(img => {
            // 直接使用src属性
            const imgUrl = img.src;

            if (imgUrl && !imgUrl.includes('data:image')) { // 排除base64图片
              // 生成文件名
              let filename;
              if (img.alt && img.alt.trim()) {
                filename = `${img.alt.replace(/[/\\?%*:|"<>]/g, '-')}`;
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

              console.log('Debug: Downloading image:', imgUrl);
              chrome.runtime.sendMessage({
                action: 'downloadImage',
                url: imgUrl,
                filename: filename
              });
            }
          });
        }
      }
    }
  }

  // 处理 reuters.com
  else if (window.location.hostname.includes("reuters.com")) {
    const articleBody = document.querySelector('[data-testid="ArticleBody"]');
    const article = document.querySelector('article[data-testid="Article"]');
    if (articleBody && article) {
      // 1. 按 DOM 顺序一次性抓取所有 Heading 和 段落
      const contentNodes = articleBody.querySelectorAll(
        'h2[data-testid="Heading"], [data-testid^="paragraph-"]'
      );
      const textLines = Array.from(contentNodes)
        .map(el => el.textContent.trim())
        .filter(t => t.length > 0);
      textContent = textLines.join('\n\n');

      // 2. 如果有正文，再去抓图片
      if (textContent) { // 或者可以改为 if (true) 来总是尝试抓取图片，即使文本内容为空
        const processedUrls = new Set();
        // 更精确地选择图片，可以先尝试轮播图图片，再尝试其他文章图片
        // 或者直接使用一个通用选择器，如果页面结构不保证所有图片都在 ArticleBody 下
        const images = Array.from(
          articleBody.querySelectorAll('img:not([sizes="110px"])')
        );
        console.log('Found images count:', images.length);

        if (images.length === 0) {
          chrome.runtime.sendMessage({ action: 'noImagesFoundInArticleBody' }); // 更明确的消息
        } else {
          images.forEach((img, idx) => {
            console.log(`Processing image ${idx}:`, img.outerHTML.substring(0, 300));

            let url = '';
            // 优先直接的 src (如果它不是一个小的内联数据URI)
            if (img.src && !img.src.startsWith('data:image/') && img.src !== window.location.href) {
              url = img.src;
            }

            // 尝试 data attributes (常见的懒加载模式)
            if (!url || url.startsWith('data:image/')) {
              url = img.dataset.src || img.getAttribute('data-src') || img.getAttribute('data-lazy-src') || '';
            }

            // 从 srcset 中选最高分辨率 (这个逻辑通常是最可靠的)
            if (img.srcset) {
              const candidates = img.srcset
                .trim().split(',')
                .map(entry => {
                  const parts = entry.trim().split(/\s+/);
                  const u = parts[0];
                  const w = parts[1] ? parts[1].replace('w', '') : '0';
                  if (!u || u.startsWith('data:image/')) return { url: u, width: 0 };
                  return { url: u, width: parseInt(w) || 0 };
                })
                .filter(c => c.width > 0 && c.url && !c.url.startsWith('data:image/'))
                .sort((a, b) => b.width - a.width);
              if (candidates.length > 0 && candidates[0].url) {
                url = candidates[0].url; // srcset 的高优先级
              }
            }

            // 如果 URL 是相对路径, 转换为绝对路径
            if (url && url.startsWith('/')) {
              try {
                url = new URL(url, window.location.origin).href;
              } catch (e) {
                console.error('Error creating absolute URL:', e);
                url = ''; // 无效的相对URL
              }
            }

            url = url.replace(/\s+/g, ''); // 清理URL中的任何空格 (理论上不应存在)

            if (!url || url.startsWith('data:image/') || url === window.location.href) { // 最终检查
              console.log(`Image ${idx} skipped: no valid/usable URL found. Final URL attempt: '${url}'`);
              return; // 跳过这个图片
            }

            if (processedUrls.has(url)) {
              console.log(`Image ${idx} skipped: URL already processed: ${url}`);
              return;
            }
            processedUrls.add(url);

            // --- 改进的标题提取逻辑 ---
            let caption = '';
            // 优先尝试 Figure > Figcaption 结构 (常见于主图)
            const figureElement = img.closest('figure[data-testid="Figure"]');
            if (figureElement) {
              const captionSpan = figureElement.querySelector('[data-testid="Caption"] span, figcaption span'); // 更通用的选择器
              if (captionSpan && captionSpan.textContent) {
                caption = captionSpan.textContent;
              }
            }

            // 如果上述未找到，尝试原始代码中的逻辑 (可能针对特定但不太标准的结构)
            // 但要注意 img.closest('[data-testid="primary-image"]') 的用法
            // primary-image 通常是图片容器，其父元素未必是标题的直接容器
            if (!caption) {
              const primaryImageDiv = img.closest('[data-testid="primary-image"]');
              const figForPrimary = primaryImageDiv ? primaryImageDiv.closest('figure') : null; // primary-image 可能在 figure 内
              const actualFig = figForPrimary || img.closest('figure'); // 回退到任意 figure

              if (actualFig) {
                // 尝试从 actualFig 的父元素或兄弟元素找 span (如原始逻辑，但要小心)
                // 或者更可能是 actualFig 的子元素 (如 figcaption)
                const spanInParent = actualFig.parentElement ? actualFig.parentElement.querySelector('span') : null;
                // 这里需要更精确的判断，这个 span 是否真的是标题
                // 这是一个非常脆弱的选择器，除非 DOM 结构非常固定且已知
                // if (spanInParent && spanInParent.textContent.length > 10 && !spanInParent.querySelector('a, button')) { // 粗略判断
                //    caption = spanInParent.textContent;
                // }
                // 更安全的还是依赖 figcaption 或 alt
              }
            }

            if (caption) { // 清理提取到的 caption
              caption = caption.replace(/REUTERS\/.*/i, '')
                .replace(/^["“]+|["”]+$/g, '')
                .trim();
            }

            // Fallback to alt text
            if (!caption && img.alt) {
              caption = img.alt.trim();
            }
            // --- 结束标题提取 ---

            const extMatch = url.match(/\.(png|jpe?g|gif|webp)(\?|$)/i);
            const ext = extMatch ? extMatch[1] : 'jpg';

            let filename = caption
              ? caption.replace(/[/\\?%*:|"<>]/g, '-').substring(0, 180) // 缩短一点以防路径过长
              : `reuters-image-${Date.now()}-${idx}`;
            filename = filename + '.' + ext;

            console.log(`Image ${idx} attempting download. URL: ${url}, Filename: ${filename}, Caption: '${caption}'`);
            chrome.runtime.sendMessage({
              action: 'downloadImage',
              url: url,
              filename: filename
            });
          });
        }
      }
    } else if (window.location.pathname.includes('/pictures/')) {
      // 2.1 抓文字描述（SingleImageHero 顶部描述）
      let textContent = '';
      const heroDesc = document.querySelector(
        'div[data-testid="SingleImageHeroSubSection"] p[data-testid="Body"]'
      );
      if (heroDesc) {
        textContent = heroDesc.textContent.trim();
        // 如果你要把文字传给 background，再发一条消息
        chrome.runtime.sendMessage({ action: 'sendText', text: textContent });
      }

      // 2.2 抓所有图片
      const processedUrls = new Set();
      // 选出 hero 图 和 event-gallery 图集里的 <img>
      const images = Array.from(
        document.querySelectorAll(
          'div[data-testid="SingleImageHero"] img, ' +
          'div[data-testid="EventGalleryImageImage"] img'
        )
      );
      console.log('Pictures page: found images count:', images.length);

      images.forEach((img, idx) => {
        // —— 复用你原来的 URL 提取逻辑 —————————————————————
        let url = '';
        if (img.src && !img.src.startsWith('data:image/') && img.src !== window.location.href) {
          url = img.src;
        }
        if ((!url || url.startsWith('data:image/')) && img.dataset.src) {
          url = img.dataset.src;
        }
        if (img.srcset) {
          const candidates = img.srcset.trim().split(',')
            .map(entry => {
              const [u, w] = entry.trim().split(/\s+/);
              return { url: u, width: parseInt(w) || 0 };
            })
            .filter(c => c.url && c.width > 0 && !c.url.startsWith('data:image/'))
            .sort((a, b) => b.width - a.width);
          if (candidates.length) url = candidates[0].url;
        }
        if (url.startsWith('/')) {
          try { url = new URL(url, location.origin).href; }
          catch (e) { url = ''; }
        }
        url = url.replace(/\s+/g, '');

        if (!url || url.startsWith('data:image/') || url === location.href) {
          console.log(`skip img ${idx}, bad url`, url);
          return;
        }
        if (processedUrls.has(url)) {
          console.log(`skip img ${idx}, dup url`, url);
          return;
        }
        processedUrls.add(url);

        // —— 针对图集页面的 Caption 提取 —————————————————————
        let caption = '';
        // 先找 figcaption 里的 span
        const fig = img.closest('figure');
        if (fig) {
          const span = fig.querySelector('figcaption span, [data-testid="ImageCaption"] span');
          if (span) caption = span.textContent.trim();
        }
        // 再 fallback 用 alt
        if (!caption && img.alt) caption = img.alt.trim();

        // 清洗 caption
        caption = caption.replace(/REUTERS\/.*/i, '')
          .replace(/^["“]+|["”]+$/g, '')
          .trim();

        // 构造文件名
        const extMatch = url.match(/\.(png|jpe?g|gif|webp)(\?|$)/i);
        const ext = extMatch ? extMatch[1] : 'jpg';
        let filename = caption
          ? caption.replace(/[/\\?%*:|"<>]/g, '-').slice(0, 180)
          : `reuters-pic-${Date.now()}-${idx}`;
        filename += '.' + ext;

        console.log(`download img ${idx}:`, url, filename, caption);
        chrome.runtime.sendMessage({
          action: 'downloadImage',
          url,
          filename
        });
      });
    }
    else {
      // 如果未找到 articleBody 或 article
      chrome.runtime.sendMessage({ action: 'articleStructureNotFound' });
    }
  }

  // 处理 nytimes.com
  else if (window.location.hostname.includes("nytimes.com")) {
    // 1. 找到文章主体
    const article = document.querySelector('main#site-content article, article#story');
    if (article) {
      const bodySection = article.querySelector('section[name="articleBody"]');
      if (bodySection) {
        // 2. 按自然顺序，收集所有 p 和 h2
        const nodes = Array.from(
          bodySection.querySelectorAll('p.css-at9mcl, p.css-at9mc1, h2')
        );
        textContent = nodes
          .map(node => node.textContent.trim())
          // 过滤空串、单字符、特殊符号开头
          .filter(t =>
            t &&
            t.length > 1 &&
            !/^[@•∞]/.test(t) &&
            t !== "Editors’ Picks"
          )
          .join('\n\n');

        // 3. 只有文本抓取成功，才继续下载图片
        if (textContent) {
          // 2. 图片：同时抓 ImageBlock-# + header 主图
          const imageBlocks = article.querySelectorAll(
            '[data-testid^="ImageBlock"], [data-testid="imageblock-wrapper"], [data-testid^="CardDeckBlock"]'
          );
          if (imageBlocks.length === 0) {
            chrome.runtime.sendMessage({ action: 'noImages' });
          } else {
            const seen = new Set();

            imageBlocks.forEach((block, blockIdx) => {
              // 2.1 收集所有 <picture>，如果有 standalone <img>（没被 <picture> 包），也加进来
              const pics = Array.from(block.querySelectorAll('picture'));
              Array.from(block.querySelectorAll('img'))
                .filter(img => !img.closest('picture'))
                .forEach(img => pics.push(img));

              pics.forEach((picOrImg, picIdx) => {
                // --- 选最高分辨率 URL ---
                let url = '';
                if (picOrImg.tagName === 'PICTURE') {
                  picOrImg.querySelectorAll('source[srcset]').forEach(src => {
                    src.srcset
                      .split(',')
                      .map(s => s.trim().split(' ')[0])
                      .forEach(u => { if (u.length > url.length) url = u; });
                  });
                  if (!url) {
                    const img = picOrImg.querySelector('img');
                    url = img ? img.src : '';
                  }
                } else {
                  // standalone <img>
                  url = picOrImg.src || '';
                }
                if (!url) return;

                // --- 去重 ---
                const base = url.split('?')[0];
                if (seen.has(base)) return;
                seen.add(base);

                // --- 提取 Caption ---
                let caption = '';
                // 优先看同一 <figure> 下的 <figcaption>
                const figure = picOrImg.closest('figure');
                if (figure) {
                  const figcap = figure.querySelector('figcaption');
                  if (figcap) caption = figcap.textContent.trim();
                }
                // 再 fallback 到 img.alt
                if (!caption && picOrImg.tagName === 'PICTURE') {
                  const img = picOrImg.querySelector('img');
                  caption = img && img.alt ? img.alt.trim() : '';
                } else if (!caption && picOrImg.tagName === 'IMG') {
                  caption = picOrImg.alt ? picOrImg.alt.trim() : '';
                }

                // --- 生成安全文件名 ---
                const safe = str => str
                  .replace(/[/\\?%*:|"<>]/g, '-')
                  .replace(/\s+/g, ' ')
                  .trim()
                  .substring(0, 180);
                const name = caption || `nytimes-image-${Date.now()}-${blockIdx}-${picIdx}`;
                const filename = safe(name) + '.jpg';

                // --- 发送下载消息 ---
                chrome.runtime.sendMessage({
                  action: 'downloadImage',
                  url: url.trim(),
                  filename
                });
              });
            });
          }
        }
      }
    }
  }

  // 新增：Washington Post 处理
  else if (window.location.hostname.includes("washingtonpost.com")) {
    // ① 先取最可能的文章容器，fallback 到 body
    const container = document.querySelector('article') || document.body;

    // 1. 提取正文：所有 data-apitype="text" 的段落
    const paras = Array.from(container.querySelectorAll('p[data-apitype="text"]'));
    textContent = paras
      .map(p => p.textContent.trim())
      .filter(t => t && t.length > 1 && !/^[•@∞]/.test(t))
      .join('\n\n');

    // 2. 提取并下载图片
    if (textContent) {
      // 找到所有 figure
      const figures = Array.from(container.querySelectorAll('figure'));
      if (figures.length === 0) {
        chrome.runtime.sendMessage({ action: 'noImages' });
      } else {
        const processedUrls = new Set();
        const processedFiles = new Set();
        figures.forEach((fig, idx) => {
          const img = fig.querySelector('img');
          if (!img) return;

          // 拿最高分辨率的 URL
          let bestUrl = img.src;
          if (img.srcset) {
            const entries = img.srcset
              .split(',')
              .map(s => s.trim().split(/\s+/))
              .map(([url, w]) => ({ url, w: parseInt(w, 10) || 0 }))
              .sort((a, b) => b.w - a.w);
            if (entries[0] && entries[0].url) bestUrl = entries[0].url;
          }

          if (processedUrls.has(bestUrl)) return;
          processedUrls.add(bestUrl);

          // caption 或 alt 或时间戳
          let name = '';
          const capEl = fig.querySelector('figcaption');
          if (capEl) {
            name = capEl.textContent.trim();
          } else if (img.alt) {
            name = img.alt.trim();
          }
          if (!name) name = `wp-image-${Date.now()}-${idx}`;

          // 清洗文件名
          let filename = name
            .replace(/[/\\?%*:|"<>]/g, '-')
            .replace(/\s+/g, ' ')
            .trim()
            + '.jpg';
          if (filename.length > 200) {
            filename = filename.slice(0, 196) + '.jpg';
          }
          if (processedFiles.has(filename)) return;
          processedFiles.add(filename);

          chrome.runtime.sendMessage({
            action: 'downloadImage',
            url: bestUrl,
            filename
          });
        });
      }
    } else {
      chrome.runtime.sendMessage({ action: 'noImages' });
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