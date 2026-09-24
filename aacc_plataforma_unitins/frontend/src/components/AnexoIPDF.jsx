/**
 * AnexoIPDF.jsx
 *
 * Componente React que renderiza o layout oficial do Anexo I da UNITINS.
 * Deve ser envolvido por react-to-print via forwardRef.
 *
 * Props:
 *   dados: objeto retornado pelo endpoint /gerar-anexo-i/
 *     {
 *       aluno: { nome, matricula, curso, campus, semestre, turno },
 *       certificados: [{ titulo_atividade, eixo_formativo, periodo_realizacao, horas_solicitadas, horas_validadas }],
 *       total_horas_validadas,
 *       data_emissao,
 *     }
 */

import React from "react"
import logoUnitins from "../assets/logounitins.jpeg"

const AnexoIPDF = React.forwardRef(function AnexoIPDF({ dados }, ref) {
  if (!dados) return null

  const { aluno, certificados = [], total_horas_validadas, data_emissao } = dados

  // Mínimo de linhas vazias para manter a tabela com tamanho fixo
  const MIN_ROWS = 9
  const linhasVazias = Math.max(0, MIN_ROWS - certificados.length)

  const styles = {
    page: {
      fontFamily: "Arial, Helvetica, sans-serif",
      color: "#000",
      fontSize: "11.5px",
      maxWidth: "900px",
      margin: "20px auto",
      padding: "20px",
      background: "#fff",
    },
    headerImg: {
      width: "100%",
      maxWidth: "700px",
      display: "block",
      margin: "0 auto 6px auto",
    },
    sgd: {
      textAlign: "right",
      fontSize: "11px",
      marginTop: "-30px",
      marginBottom: "10px",
    },
    h1: {
      textAlign: "center",
      fontSize: "13px",
      margin: "10px 0 4px 0",
    },
    h2: {
      textAlign: "center",
      fontSize: "13px",
      margin: "0 0 18px 0",
    },
    campoLinha: {
      margin: "6px 0",
      fontSize: "12.5px",
      whiteSpace: "nowrap",
    },
    blank: {
      borderBottom: "1px solid #000",
      display: "inline-block",
    },
    table: {
      width: "100%",
      borderCollapse: "collapse",
      marginTop: "16px",
      fontSize: "11.5px",
    },
    th: {
      border: "1px solid #000",
      padding: "4px 6px",
      textAlign: "center",
      verticalAlign: "middle",
      background: "#d9d9d9",
      fontWeight: "bold",
      fontSize: "11.5px",
    },
    td: {
      border: "1px solid #000",
      padding: "4px 6px",
      textAlign: "center",
      verticalAlign: "middle",
    },
    tdVazia: {
      border: "1px solid #000",
      height: "22px",
    },
    rodapeTabela: {
      display: "flex",
      justifyContent: "center",
      gap: "60px",
      marginTop: "16px",
      fontSize: "12.5px",
    },
    encaminhamento: {
      textAlign: "center",
      marginTop: "22px",
      fontSize: "12.5px",
    },
    assinatura: {
      textAlign: "center",
      marginTop: "70px",
      fontSize: "12.5px",
    },
    assinaturaLinha: {
      borderBottom: "1px solid #000",
      width: "320px",
      margin: "0 auto 4px auto",
    },
    rodapeDocTable: {
      marginTop: "60px",
      borderCollapse: "collapse",
      width: "100%",
    },
    rodapeDocTd: {
      border: "none",
      padding: "0",
      textAlign: "left",
      verticalAlign: "top",
    },
    qrCell: {
      border: "none",
      padding: "0",
      paddingRight: "10px",
      textAlign: "left",
      verticalAlign: "top",
      width: "78px",
    },
    qrImg: {
      width: "70px",
      height: "auto",
      display: "block",
    },
    texto: {
      fontSize: "8px",
      color: "#000",
    },
  }

  return (
    <div ref={ref} style={styles.page}>
      <style type="text/css" media="print">
        {`
          @page { size: A4 landscape; margin: 15mm; }
          body { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
        `}
      </style>
      
      {/* Cabeçalho institucional */}
      <img style={styles.headerImg} src={logoUnitins} alt="Cabeçalho UNITINS / TOCANTINS" />

      <div style={styles.sgd}>SGD: {data_emissao?.replace(/\//g, "/")}</div>

      <h1 style={styles.h1}>ANEXO I</h1>
      <h2 style={styles.h2}>REQUERIMENTO DE CONTABILIZAÇÃO DE CARGA HORÁRIA PARA AS ATIVIDADES</h2>

      {/* Campos do aluno */}
      <div style={styles.campoLinha}>
        <strong>Nome do aluno</strong>:{" "}
        <span style={{ ...styles.blank, width: "480px", display: "inline-block" }}>
          {aluno?.nome ?? ""}
        </span>
        {"  "}
        <strong>Matrícula:</strong>{" "}
        <span style={{ ...styles.blank, width: "130px", display: "inline-block" }}>
          {aluno?.matricula ?? ""}
        </span>
      </div>

      <div style={styles.campoLinha}>
        <strong>Curso:</strong>{" "}
        <span style={{ ...styles.blank, width: "220px", display: "inline-block" }}>
          {aluno?.curso ?? ""}
        </span>
        {"  "}
        <strong>Câmpus:</strong>{" "}
        <span style={{ ...styles.blank, width: "150px", display: "inline-block" }}>
          {aluno?.campus ?? "Palmas - TO"}
        </span>
        {"  "}
        <strong>Semestre:</strong>{" "}
        <span style={{ ...styles.blank, width: "70px", display: "inline-block" }}>
          {aluno?.semestre ?? ""}
        </span>
        {"  "}
        <strong>Turno:</strong>{" "}
        <span style={{ ...styles.blank, width: "100px", display: "inline-block" }}>
          {aluno?.turno ?? ""}
        </span>
      </div>

      {/* Tabela de atividades */}
      <table style={styles.table}>
        <thead>
          <tr>
            <th style={{ ...styles.th, width: "32%" }}>Atividade</th>
            <th style={{ ...styles.th, width: "22%" }}>
              Especificação<br />
              (Ensino, Pesquisa ou Extensão)
            </th>
            <th style={{ ...styles.th, width: "16%" }}>Período de realização</th>
            <th style={{ ...styles.th, width: "15%" }}>Total de horas<br />(solicitadas)</th>
            <th style={{ ...styles.th, width: "15%" }}>Total de horas<br />(validadas)</th>
          </tr>
        </thead>
        <tbody>
          {certificados.map((cert, i) => (
            <tr key={i}>
              <td style={{ ...styles.td, textAlign: "left" }}>{cert.titulo_atividade}</td>
              <td style={styles.td}>{cert.eixo_formativo}</td>
              <td style={styles.td}>{cert.periodo_realizacao}</td>
              <td style={styles.td}>{cert.horas_solicitadas}</td>
              <td style={styles.td}>{cert.horas_validadas}</td>
            </tr>
          ))}
          {Array.from({ length: linhasVazias }).map((_, i) => (
            <tr key={`vazia-${i}`}>
              <td style={styles.tdVazia}>&nbsp;</td>
              <td style={styles.tdVazia}>&nbsp;</td>
              <td style={styles.tdVazia}>&nbsp;</td>
              <td style={styles.tdVazia}>&nbsp;</td>
              <td style={styles.tdVazia}>&nbsp;</td>
            </tr>
          ))}
        </tbody>
      </table>

      {/* Rodapé da tabela */}
      <div style={styles.rodapeTabela}>
        <div>
          <strong>Local:</strong>{" "}
          <span style={{ ...styles.blank, width: "250px", display: "inline-block" }}>
            {aluno?.campus ?? "Palmas - TO"}
          </span>
        </div>
        <div>
          <strong>Data:</strong>{" "}
          <span style={{ ...styles.blank, width: "100px", display: "inline-block" }}>
            {data_emissao ?? ""}
          </span>
        </div>
      </div>

      {/* Encaminhamento */}
      <div style={styles.encaminhamento}>
        Encaminhe-se à Secretária Acadêmica para lançamento do total de{" "}
        <span style={{ ...styles.blank, width: "50px", display: "inline-block" }}>
          {total_horas_validadas}
        </span>{" "}
        horas atividades no histórico do acadêmico.
      </div>

      {/* Assinatura */}
      <div style={styles.assinatura}>
        <div style={styles.assinaturaLinha} />
        Coordenação do Curso (assinatura digital)
      </div>

      {/* Rodapé do documento */}
      <table style={styles.rodapeDocTable}>
        <tbody>
          <tr>
            <td style={styles.qrCell}>
              {/* QR code placeholder — substituir por QR real se necessário */}
              <div
                style={{
                  width: 70,
                  height: 70,
                  border: "1px solid #ccc",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontSize: "8px",
                  color: "#888",
                }}
              >
                QR
              </div>
            </td>
            <td style={styles.rodapeDocTd}>
              <div style={styles.texto}>
                <p>
                  Documento gerado eletronicamente pelo Sistema AACC &mdash; Unitins em{" "}
                  {data_emissao ?? ""}.
                </p>
                <p>A autenticidade pode ser verificada junto à Secretaria Acadêmica.</p>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  )
})

export default AnexoIPDF
