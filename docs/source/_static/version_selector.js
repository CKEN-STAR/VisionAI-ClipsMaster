// Version selector for VisionAI-ClipsMaster documentation
document.addEventListener('DOMContentLoaded', function() {
  // Fetch version configuration from JSON file
  fetch('/configs/docs_version.json')
    .then(response => response.json())
    .then(data => {
      createVersionSelector(data);
    })
    .catch(error => {
      console.error('Error loading version data:', error);
    });
  
  function createVersionSelector(versionData) {
    const currentVersion = versionData.current_version;
    const languages = versionData.languages;
    const publishedVersions = versionData.published_versions;
    const devVersion = versionData.dev_version;
    const versionAliases = versionData.version_aliases;
    
    // Get current language from URL or default to first supported language
    const currentPath = window.location.pathname;
    let currentLanguage = languages[0];
    for (const lang of languages) {
      if (currentPath.includes(`/${lang}/`)) {
        currentLanguage = lang;
        break;
      }
    }
    
    // Create version selector container
    const header = document.querySelector('.md-header__inner');
    if (!header) return;
    
    const selectorContainer = document.createElement('div');
    selectorContainer.className = 'md-version-select';
    selectorContainer.style.cssText = 'margin-right: 1rem; position: relative;';
    
    // Create the dropdown
    const select = document.createElement('select');
    select.className = 'md-version-select__dropdown';
    select.style.cssText = 'background-color: var(--md-primary-bg-color); color: var(--md-primary-fg-color); padding: 0.5rem; border-radius: 4px; border: none;';
    
    // Add development version if it exists
    if (devVersion) {
      const devOption = document.createElement('option');
      devOption.value = `/${currentLanguage}${devVersion.path}`;
      devOption.text = `${devVersion.version} (${devVersion.description})`;
      select.appendChild(devOption);
    }
    
    // Add all published versions
    publishedVersions.forEach(version => {
      const option = document.createElement('option');
      option.value = `/${currentLanguage}${version.path}`;
      
      // Mark current version
      if (version.version === currentVersion) {
        option.selected = true;
        option.text = `${version.version} (${version.code_name}) - 当前版本`;
      } else {
        option.text = `${version.version} (${version.code_name})`;
      }
      
      // Add support status indicator
      if (!version.supported) {
        option.text += ' - 不再支持';
      }
      
      select.appendChild(option);
    });
    
    // Handle version change
    select.addEventListener('change', function() {
      window.location.href = this.value;
    });
    
    selectorContainer.appendChild(select);
    
    // Add version selector to header
    const searchBox = document.querySelector('.md-search');
    if (searchBox && searchBox.parentNode) {
      searchBox.parentNode.insertBefore(selectorContainer, searchBox);
    } else {
      header.appendChild(selectorContainer);
    }
    
    // Add version info to footer
    const footer = document.querySelector('.md-footer-meta');
    if (footer) {
      const versionInfo = document.createElement('div');
      versionInfo.className = 'md-footer-version';
      versionInfo.innerHTML = `<p>当前版本: ${currentVersion} | <a href="/${currentLanguage}/${versionAliases.latest}/">最新版</a> | <a href="/${currentLanguage}/${versionAliases.stable}/">稳定版</a></p>`;
      footer.appendChild(versionInfo);
    }
  }
}); 