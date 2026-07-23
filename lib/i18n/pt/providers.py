"""Traduções em português brasileiro para metadados do registro de provedores."""

MESSAGES: dict[str, str] = {
    # Provider display names
    "provider_name_gemini-aistudio": "AI Studio",
    "provider_name_gemini-vertex": "Vertex AI",
    "provider_name_ark": "Volcengine Ark",
    "provider_name_ark-agent-plan": "Volcengine Ark Agent Plan",
    "provider_name_grok": "Grok",
    "provider_name_openai": "OpenAI",
    "provider_name_vidu": "Vidu",
    "provider_name_dashscope": "Alibaba Model Studio",
    "provider_name_minimax": "MiniMax",
    "provider_name_kling": "Kling",
    "provider_name_agnes": "Agnes",
    # Provider descriptions
    "provider_desc_gemini-aistudio": "O Google AI Studio oferece modelos Gemini com geração de imagem e vídeo, ideal para prototipagem rápida e projetos pessoais.",
    "provider_desc_gemini-vertex": "Plataforma empresarial Google Cloud Vertex AI com suporte a Gemini e Imagen, cotas maiores e geração de áudio.",
    "provider_desc_ark": "Plataforma de IA Volcengine Ark da ByteDance com geração de vídeo Seedance e imagem Seedream, com áudio e controle de seed.",
    "provider_desc_ark-agent-plan": "O Volcengine Ark Agent Plan agrega Doubao e outros modelos principais para geração de texto, imagem e vídeo.",
    "provider_desc_grok": "Modelos Grok da xAI com suporte a geração de vídeo e imagem.",
    "provider_desc_openai": "Plataforma OpenAI com suporte a texto GPT-5.4, GPT Image e geração de vídeo Sora.",
    "provider_desc_vidu": "Plataforma de vídeo Shengshu Vidu com texto-para-vídeo, imagem-para-vídeo, primeiro-último frame, referência-para-vídeo e referência-para-imagem. Apenas imagem e vídeo.",
    "provider_desc_dashscope": "Plataforma multimodal Alibaba Cloud Model Studio (DashScope) com texto Qwen, imagens Qwen-Image / Wan e vídeo HappyHorse / Wan (incluindo referência-para-vídeo).",
    "provider_desc_minimax": "Plataforma multimodal MiniMax (Hailuo) com geração de texto, imagem e vídeo. Conecta ao site doméstico por padrão; defina base_url para o site internacional no exterior.",
    "provider_desc_kling": "Plataforma de vídeo e imagem Kuaishou Kling. Autenticação por API Key funciona com todos os modelos; Access Key + Secret Key (JWT) só suporta modelos 3.0 e anteriores. Escolha um — quando ambos estão definidos, a API Key tem prioridade.",
    "provider_desc_agnes": "Plataforma multimodal Agnes (estilo OpenAI), autenticada com chave API Bearer; atualmente suporta geração de imagem, texto e vídeo.",
    # Agent preset notes
    "preset_notes_deepseek": "Endpoint oficial Anthropic-compat da DeepSeek; precisa de chave com prefixo sk-.",
    "preset_notes_xiaomi_mimo": "Xiaomi MiMo só aceita nomes de modelo conhecidos; sem lista pública de modelos.",
    "preset_notes_ark_coding_plan": "Volcengine Ark Coding Plan",
    "preset_notes_ark_agent_plan": "Volcengine Ark Agent Plan",
}
