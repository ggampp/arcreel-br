
export default {
  'unknown_error': 'Ocorreu um erro desconhecido',
  'network_error': 'Erro de rede, verifique sua conexão',
  'unauthorized': 'Não autorizado, faça login novamente',
  'forbidden': 'Permissão negada',
  'not_found': 'Recurso não encontrado',
  'server_error': 'Erro do servidor, tente novamente mais tarde',
  'validation_error': 'Falha na validação',
  'source_unsupported_format': 'Formato de origem não suportado: {{ext}}',
  'source_decode_failed': 'Falha ao decodificar "{{filename}}" (tentativas: {{tried}})',
  'source_corrupt_file': 'O arquivo de origem "{{filename}}" não pode ser analisado: {{reason}}',
  'source_too_large': 'O arquivo de origem "{{filename}}" é muito grande ({{size_mb}} MB > {{limit_mb}} MB)',
  'source_conflict': 'O arquivo de origem "{{existing}}" já existe',
  // Image Capability
  'image_endpoint_mismatch_no_i2i': 'O modelo {{model}} só suporta texto-para-imagem (sem /v1/images/edits)',
  'image_endpoint_mismatch_no_t2i': 'O modelo {{model}} só suporta imagem-para-imagem (imagens de referência obrigatórias)',
  'image_capability_missing_i2i': '{{provider}}/{{model}} não suporta imagem-para-imagem; configure um modelo padrão com edição de imagem',
  'image_capability_missing_t2i': '{{provider}}/{{model}} não suporta texto-para-imagem; configure um modelo padrão com texto-para-imagem',
};
