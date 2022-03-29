module.exports = ({ marp }) =>
  marp.use(require('markdown-it-plantuml'), {
    // Wrap in <p> for better rendering in some built-in themes
    render: (...args) =>
      `<p>${marp.markdown.renderer.rules.image(...args)}</p>`,
  })