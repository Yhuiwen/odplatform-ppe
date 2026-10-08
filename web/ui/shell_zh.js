// Translate Streamlit's shell without replacing React-owned elements or handlers.
(() => {
  const key = '__ppeShellChineseObserver';
  if (window[key]) {
    window[key].refresh();
    return;
  }
  const translations = new Map(Object.entries({
    'Deploy': '部署',
    'Main menu': '主菜单',
    'Theme': '主题',
    'System': '跟随系统',
    'Light': '浅色',
    'Dark': '深色',
    'Rerun': '重新运行',
    'Auto rerun': '自动重新运行',
    'Clear cache': '清除缓存',
    'Print': '打印',
    'Record screen': '录制屏幕',
    'Cancel recording': '取消录制',
    'Stop recording': '停止录制',
    'Made with': '基于',
    'Made with Streamlit v': '基于 Streamlit，版本 ',
    'Copy version to clipboard': '复制版本号',
    'Deploy this app using...': '选择应用部署方式',
    'Streamlit Community Cloud': 'Streamlit 社区云',
    'For community, always free': '面向社区，永久免费',
    'For personal hobbies and learning': '适合个人兴趣项目与学习',
    'Deploy unlimited public apps': '可部署不限数量的公开应用',
    'Explore and learn from Streamlit’s community and popular apps': '探索 Streamlit 社区与热门应用，交流学习',
    'For enterprise': '面向企业',
    'Enterprise-level security, support, and fully managed infrastructure': '企业级安全与支持，以及全面托管的基础设施',
    'Deploy unlimited private apps with role-based sharing': '可部署不限数量的私有应用，并按角色共享',
    'Integrate with Snowflake’s full data stack': '与 Snowflake 完整数据平台集成',
    'Other platforms': '其他平台',
    'For custom deployment': '适合自定义部署',
    'Deploy on your own hardware or cloud service': '部署到自己的硬件或云服务',
    'Set up and maintain your own authentication, resources, and costs': '自行配置和维护身份验证、资源及费用',
    'Deploy now': '立即部署',
    'Learn more': '了解更多',
    'Start trial': '开始试用',
    'Close': '关闭',
    'Streamlit Logo': 'Streamlit 标志',
    'Checkmark': '支持',
    'Rocket': '火箭',
  }));
  const selector = '[data-testid="stToolbar"], [data-testid="stMainMenuPopover"], '
    + '[role="dialog"]:has([data-testid^="stDeployDialog"])';

  function translate(text) {
    const normalized = text.trim().replace(/\s+/g, ' ');
    let replacement = translations.get(normalized);
    if (!replacement && /^Made with Streamlit v\s*[\d.]+$/.test(normalized)) {
      replacement = normalized.replace('Made with Streamlit v', '基于 Streamlit，版本 ');
    }
    return replacement ? text.replace(text.trim(), replacement) : text;
  }

  function refresh() {
    for (const root of document.querySelectorAll(selector)) {
      const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
      let node;
      while ((node = walker.nextNode())) {
        if (node.parentElement.closest('script, style, [translate="no"]')) continue;
        const translated = translate(node.data);
        if (translated !== node.data) node.data = translated;
      }
      for (const element of [root, ...root.querySelectorAll('[aria-label], [title], [alt]')]) {
        for (const attribute of ['aria-label', 'title', 'alt']) {
          const original = element.getAttribute(attribute);
          if (!original) continue;
          const translated = translate(original);
          if (translated !== original) element.setAttribute(attribute, translated);
        }
      }
    }
  }

  let scheduled = false;
  const observer = new MutationObserver(records => {
    const relevant = records.some(record => {
      const element = record.target.nodeType === Node.ELEMENT_NODE
        ? record.target : record.target.parentElement;
      return element?.closest(selector) || [...record.addedNodes].some(node =>
        node.nodeType === Node.ELEMENT_NODE && (node.matches(selector) || node.querySelector(selector)));
    });
    if (!relevant || scheduled) return;
    scheduled = true;
    requestAnimationFrame(() => { scheduled = false; refresh(); });
  });
  observer.observe(document.body, {
    childList: true, subtree: true, characterData: true,
    attributes: true, attributeFilter: ['aria-label', 'title', 'alt'],
  });
  window[key] = { observer, refresh };
  refresh();
})();
