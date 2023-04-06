const nodes = document.querySelectorAll(".timeago");
if (nodes.length > 0) {
  const locale = nodes[0].getAttribute("locale");
  timeago.render(nodes, locale);
}