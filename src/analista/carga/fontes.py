ENCODING = "latin-1"
DELIMITADOR = ";"

URL_CADASTRO = "https://dados.cvm.gov.br/dados/CIA_ABERTA/CAD/DADOS/cad_cia_aberta.csv"

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