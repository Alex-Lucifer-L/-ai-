const form = document.querySelector("#askForm");
const questionInput = document.querySelector("#question");
const topKInput = document.querySelector("#topK");
const dryRunInput = document.querySelector("#dryRun");
const submitButton = document.querySelector("#submitButton");
const answerEl = document.querySelector("#answer");
const answerStateEl = document.querySelector("#answerState");
const referencesEl = document.querySelector("#references");
const referenceCountEl = document.querySelector("#referenceCount");
const modelNameEl = document.querySelector("#modelName");
const sampleButtons = document.querySelectorAll(".sample");

async function loadHealth() {
  try {
    const response = await fetch("/api/health");
    const data = await response.json();
    modelNameEl.textContent = data.llm_model || "未配置";
  } catch (error) {
    modelNameEl.textContent = "连接失败";
  }
}

function setLoading(isLoading) {
  submitButton.disabled = isLoading;
  submitButton.querySelector("span:last-child").textContent = isLoading ? "回答中" : "开始回答";
  answerStateEl.textContent = isLoading ? "生成中" : "已完成";
}

function setError(message) {
  answerEl.className = "answer error";
  answerEl.textContent = message;
  answerStateEl.textContent = "出错";
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function renderAnswer(answer) {
  answerEl.className = "answer";
  answerEl.textContent = answer || "没有返回回答。";
}

function renderReferences(references) {
  referenceCountEl.textContent = `${references.length} 条`;

  if (!references.length) {
    referencesEl.className = "references empty";
    referencesEl.textContent = "暂无引用。";
    return;
  }

  referencesEl.className = "references";
  referencesEl.innerHTML = references
    .map((reference, index) => {
      const title = escapeHtml(reference.item_name || reference.source_title || "未命名政策");
      const category = escapeHtml(reference.category_name || "未分类");
      const regions = escapeHtml(reference.regions || "未标明地区");
      const excerpt = escapeHtml(reference.original_excerpt || "暂无原文片段。");
      const url = escapeHtml(reference.source_url || "#");

      return `
        <article class="reference-card">
          <h3>${index + 1}. ${title}</h3>
          <div class="meta">
            <span class="tag">${category}</span>
            <span class="tag">${regions}</span>
            <span class="tag">item#${escapeHtml(reference.item_id)}</span>
          </div>
          <div class="excerpt">${excerpt}</div>
          <a class="source-link" href="${url}" target="_blank" rel="noreferrer">查看官方来源</a>
        </article>
      `;
    })
    .join("");
}

async function askQuestion(event) {
  event.preventDefault();
  const question = questionInput.value.trim();
  const topK = Number(topKInput.value || 3);

  if (!question) {
    setError("请输入你的政策问题。");
    return;
  }

  answerEl.className = "answer empty";
  answerEl.textContent = "正在检索本地数据库并生成回答...";
  renderReferences([]);
  setLoading(true);

  try {
    const response = await fetch("/api/ask", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        question,
        top_k: topK,
        dry_run: dryRunInput.checked,
      }),
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || "请求失败。");
    }

    renderAnswer(data.answer);
    renderReferences(data.references || []);
  } catch (error) {
    setError(error.message);
  } finally {
    setLoading(false);
  }
}

sampleButtons.forEach((button) => {
  button.addEventListener("click", () => {
    sampleButtons.forEach((item) => item.classList.remove("active"));
    button.classList.add("active");
    questionInput.value = button.dataset.question;
    questionInput.focus();
  });
});

form.addEventListener("submit", askQuestion);
loadHealth();
