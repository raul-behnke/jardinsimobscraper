import * as OpenAI from "openai";
import dotenv from "dotenv";

dotenv.config();

const configuration = new OpenAI.Configuration({
  apiKey: process.env.OPENAI_API_KEY,
});
const openai = new OpenAI.OpenAIApi(configuration);

// Resto do código...


// System instruction com as regras para o agente de Markdown
const systemPrompt = `
# 🏠 Markdown Real Estate Summarizer | Especialista em Listagem Imobiliária

Você é um agente altamente especializado em extração pontual de dados estruturados para a geração automática e profissional de resumos individuais de imóveis a partir de arquivos JSON fornecidos.

✅ **Sequência lógica obrigatória ("chain-of-thought"):**

## 1️⃣ Análise detalhada do JSON por entrada individual
Analise cuidadosamente cada registro contido no JSON, identificando obrigatoriamente todas estas informações, quando disponíveis:

- 📌 **Título ou descrição principal do imóvel**
- 💰 **Preço, valor total ou valor do aluguel**
- 📍 **Localização/endereço detalhado**
- 📐 **Área (metragem quadrada)**
- 🛏️ **Quantidade de Quartos**
- 🛁 **Quantidade de Banheiros**
- 🚗 **Vagas de Garagem**
- 🔖 **Características especiais ou diferenciais destacados**
- 🔗 **Link completo para mais informações**

**Atenção:** mantenha absoluta fidelidade, sem inferências ou acréscimo de detalhes não explicitamente presentes no JSON fornecido.

## 2️⃣ Estruturação precisa no formato Markdown otimizado
Obrigatoriamente apresente cada imóvel em um resumo individual, estruturado rigorosamente no seguinte template otimizado Markdown:

\`\`\`markdown
## 🏡 [Título ou Descrição Principal]

- 💰 **Valor:** [preço claramente evidenciado, formato visual amigável]
- 📍 **Localização:** [endereço completo ou localização destacada]
- 📐 **Área:** [metragem claramente especificada, ex: 85m²]
- 🛏️ **Quartos:** [quantidade especificada ou "não informado"]
- 🛁 **Banheiros:** [quantidade especificada ou "não informado"]
- 🚗 **Vagas:** [quantidade especificada ou "não informado"]
- 🔗 **Link:** [coloque o link completo clicável aqui]

### 🎯 Características/Diferenciais:
- [Características relevantes]
- [Diferencial do imóvel, quando aplicável]
- [Outras informações claramente identificadas]

---
\`\`\`
`;

/**
 * Função que envia um registro (JSON) para a API e retorna o resumo em Markdown.
 * @param {Object} record - Registro do imóvel
 * @param {string} category - Nome da categoria (para reforçar no prompt, se necessário)
 * @returns {Promise<string>} Resumo formatado em Markdown
 */
async function summarizeRecord(record, category) {
  // Monta o prompt com os dados do imóvel
  const userPrompt = `Categoria: ${category}
Dados do imóvel:
${JSON.stringify(record, null, 2)}
`;

  try {
    const response = await openai.createChatCompletion({
      model: "gpt-3.5-turbo", // ou "gpt-4", se disponível
      messages: [
        { role: "system", content: systemPrompt },
        { role: "user", content: userPrompt }
      ],
      temperature: 0.3,
      max_tokens: 500,
    });

    const markdown = response.data.choices[0].message.content;
    return markdown;
  } catch (error) {
    console.error("Erro ao resumir registro:", error);
    return "";
  }
}

/**
 * Função que processa um arquivo JSON e retorna os resumos concatenados.
 * @param {string} inputFile - Caminho do arquivo JSON (ex.: "casas.json")
 * @param {string} category - Nome da categoria (ex.: "Casas")
 * @returns {Promise<string>} Resumos concatenados
 */
async function processFile(inputFile, category) {
  try {
    const rawData = fs.readFileSync(inputFile, "utf8");
    const records = JSON.parse(rawData);
    let markdownOutput = `\n# Resumo da Categoria: ${category}\n\n`;
    
    for (const record of records) {
      console.log(`Processando registro ${record.listingID || "sem ID"} da categoria ${category}...`);
      const summary = await summarizeRecord(record, category);
      markdownOutput += summary + "\n\n";
    }
    return markdownOutput;
  } catch (error) {
    console.error(`Erro ao processar o arquivo ${inputFile}:`, error);
    return "";
  }
}

async function main() {
  // Lista com as categorias e os respectivos arquivos JSON
  const categories = [
    { file: "casas.json", category: "Casas" },
    { file: "apartamentos.json", category: "Apartamentos" },
    { file: "geminados.json", category: "Geminados" },
    { file: "sobrados.json", category: "Sobrados" },
    // Adicione mais categorias conforme necessário
  ];

  let finalSummary = "";
  // Processa cada arquivo e acumula os resumos
  for (const { file, category } of categories) {
    console.log(`Iniciando o processamento da categoria: ${category}`);
    const summary = await processFile(file, category);
    finalSummary += summary + "\n";
  }

  // Grava todos os resumos em um único arquivo TXT
  fs.writeFileSync("final_summary.txt", finalSummary);
  console.log("Arquivo 'final_summary.txt' gerado com sucesso!");
}

main().catch(console.error);
