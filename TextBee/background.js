chrome.action.onClicked.addListener(async (tab) => {
  if (tab.url.includes("ft.com") || tab.url.includes("bloomberg.com")) {
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
    const bodyContent = document.querySelector('.body-content');
    if (bodyContent) {
      // 修改选择器以更准确地匹配目标段落
      const paragraphs = bodyContent.querySelectorAll('p[class*="media-ui-Paragraph_text"][class*="paywall"]');

      textContent = Array.from(paragraphs)
        .map(p => p.textContent.trim())
        .filter(text => {
          // 增强过滤条件
          return text &&
            text.length > 1 &&
            !['@', '•', '∞', '.'].includes(text) &&
            !/^\s*$/.test(text); // 过滤纯空白内容
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
  // 创建通知样式
  const style = document.createElement('style');
  style.textContent = `
    .copy-notification {
    position: fixed;
    top: 20px;
      left: 50%;         /* 修改：从right改为left:50% */
      transform: translateX(-50%) translateY(-20px); /* 修改：添加translateX实现水平居中 */
    background-color: rgba(76, 175, 80, 0.9);
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
    notification.style.transform = 'translateX(-50%) translateY(0)'; // 修改：保持水平居中的同时添加垂直动画
  });

  // 3秒后淡出
  setTimeout(() => {
    notification.style.opacity = '0';
    notification.style.transform = 'translateX(-50%) translateY(-20px)'; // 修改：保持水平居中的同时添加淡出动画
    setTimeout(() => {
      notification.remove();
      style.remove();
    }, 300);
  }, 3000);
}