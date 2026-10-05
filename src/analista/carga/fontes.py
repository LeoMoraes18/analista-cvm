ENCODING = "latin-1"
DELIMITADOR = ";"

URL_CADASTRO = "https://dados.cvm.gov.br/dados/CIA_ABERTA/CAD/DADOS/cad_cia_aberta.csv"
URL_DFP = "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/DFP/DADOS/dfp_cia_aberta_{ano}.zip"

# coluna do CSV -> coluna da tabela
COLUNAS_CADASTRO = {
    "CD_CVM": "cd_cvm",
    "CNPJ_CIA": "cnpj",
    "DENOM_SOCIAL": "denom_social",
    "DENOM_COMERC": "denom_comerc",
    "SETOR_ATIV": "setor_ativ",
    "SIT": "situacao",
    "DT_REG": "dt_registro",
    "DT_CANCEL": "dt_cancelamento",
    "UF": "uf",
}

# (demonstração, consolidado) -> trecho do nome do arquivo dentro do zip
ARQUIVOS_DFP = {
    ("DRE", True): "DRE_con",
    ("DRE", False): "DRE_ind",
}

COLUNAS_BRUTO = (
    "DT_REFER", "VERSAO", "CD_CVM", "ESCALA_MOEDA", "ORDEM_EXERC",
    "DT_INI_EXERC", "DT_FIM_EXERC", "CD_CONTA", "DS_CONTA", "VL_CONTA",
)