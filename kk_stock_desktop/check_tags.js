const fs = require('fs');

function checkVueComponentTags(content) {
  const stack = [];
  const selfClosingTags = new Set(['img', 'br', 'hr', 'input', 'meta', 'link', 'area', 'base', 'col', 'embed', 'source', 'track', 'wbr']);
  
  // 匹配所有标签，包括Vue组件
  const tagRegex = /<\/?([a-zA-Z][a-zA-Z0-9-]*)[^>]*>/g;
  let match;
  let lineNumber = 1;
  let lastIndex = 0;
  
  while ((match = tagRegex.exec(content)) !== null) {
    // 计算行号
    const beforeMatch = content.substring(lastIndex, match.index);
    lineNumber += (beforeMatch.match(/\n/g) || []).length;
    lastIndex = match.index;
    
    const fullTag = match[0];
    const tagName = match[1].toLowerCase();
    const isClosing = fullTag.startsWith('</');
    const isSelfClosing = fullTag.endsWith('/>');
    
    console.log(`Line ${lineNumber}: ${fullTag}`);
    
    if (isClosing) {
      // 闭合标签
      if (stack.length === 0) {
        console.log(`ERROR: Unexpected closing tag ${fullTag} at line ${lineNumber}`);
        return false;
      }
      const lastTag = stack.pop();
      if (lastTag.name !== tagName) {
        console.log(`ERROR: Mismatched tags at line ${lineNumber}. Expected </${lastTag.name}>, found ${fullTag}. Opening tag was at line ${lastTag.line}`);
        return false;
      }
    } else if (!isSelfClosing && !selfClosingTags.has(tagName)) {
      // 开始标签（非自闭合）
      stack.push({ name: tagName, line: lineNumber, tag: fullTag });
    }
  }
  
  if (stack.length > 0) {
    console.log(`ERROR: Unclosed tags:`);
    stack.forEach(tag => {
      console.log(`  - <${tag.name}> at line ${tag.line}: ${tag.tag}`);
    });
    return false;
  }
  
  console.log('All tags are properly matched!');
  return true;
}

// 读取Dashboard.vue文件
const filePath = './src/views/Dashboard.vue';
const content = fs.readFileSync(filePath, 'utf8');

// 提取template部分
const templateMatch = content.match(/<template[^>]*>([\s\S]*?)<\/template>/);
if (templateMatch) {
  console.log('Checking template tags...');
  checkVueComponentTags(templateMatch[1]);
} else {
  console.log('No template found');
}