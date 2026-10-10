import math
import statistics

LINHA = "-" * 53



class ErroEntrada(Exception):
    """Erro de leitura ou validação dos dados informados."""


def validar_minimo(dados):
    if len(dados) < 2:
        raise ErroEntrada("São necessários pelo menos 2 valores numéricos.")
    return dados


def ler_terminal():
    """Lê números separados por vírgula digitados no terminal."""

    texto = input("Digite os valores separados por vírgula: ")
    dados, invalidos = [], []
    for t in (t.strip() for t in texto.split(",") if t.strip()):
        try:
            dados.append(float(t))
        except ValueError:
            invalidos.append(t)
    if invalidos:
        raise ErroEntrada(f"Valores não numéricos encontrados: {invalidos}")
    return validar_minimo(dados)


def ler_csv(caminho):
    """Lê números de um .csv (separador ',' ou ';'; cabeçalho opcional)."""

    try:
        with open(caminho, encoding="utf-8-sig") as arq:
            linhas = [l.strip() for l in arq if l.strip()]
    except FileNotFoundError:
        raise ErroEntrada(f"Arquivo não encontrado: {caminho}")
    except (OSError, UnicodeDecodeError) as e:
        raise ErroEntrada(f"Não foi possível ler o arquivo: {e}")

    dados, invalidos = [], []
    for num, linha in enumerate(linhas, start=1):
        if ";" in linha:  # padrão brasileiro: decimal com vírgula
            tokens = [t.strip().replace(",", ".") for t in linha.split(";")]
        else:
            tokens = [t.strip() for t in linha.split(",")]
        valores, ruins = [], []
        for t in tokens:
            if not t:
                continue
            try:
                valores.append(float(t))
            except ValueError:
                ruins.append(t)
        if num == 1 and ruins and not valores:
            continue  # primeira linha sem números = cabeçalho
        dados.extend(valores)
        invalidos.extend(f"linha {num}: '{r}'" for r in ruins)
    if invalidos:
        raise ErroEntrada(f"Valores não numéricos no arquivo: {invalidos}")
    return validar_minimo(dados)

def parte1(dados):
    print(f"Média: {statistics.mean(dados):.2f}")
    print(f"Mediana: {statistics.median(dados):.2f}")
    print(f"Moda: {statistics.mode(dados):.2f}")

def tabela_frequencias(dados):
    """Retorna lista de (xi, fi, Fi) ordenada por xi."""

    contagem = {}
    for v in dados:
        contagem[v] = contagem.get(v, 0) + 1
    tabela, acum = [], 0
    for xi in sorted(contagem):
        acum += contagem[xi]
        tabela.append((xi, contagem[xi], acum))
    return tabela

def media_discreta(tabela):
    return sum(xi * fi for xi, fi, _ in tabela) / tabela[-1][2]


def valor_na_posicao(tabela, pos):
    """Valor xi que ocupa a posição 'pos' (1-indexada), usando Fi."""

    for xi, _, Fi in tabela:
        if Fi >= pos:
            return xi


def mediana_discreta(tabela):
    n = tabela[-1][2]
    if n % 2:
        return valor_na_posicao(tabela, (n + 1) // 2)
    return (valor_na_posicao(tabela, n // 2)
            + valor_na_posicao(tabela, n // 2 + 1)) / 2


def modas_discreta(tabela):
    """Lista de modas (vazia se amodal)."""
    maior = max(fi for _, fi, _ in tabela)
    if len(tabela) > 1 and all(fi == maior for _, fi, _ in tabela):
        return []
    return [xi for xi, fi, _ in tabela if fi == maior]

def parte2(dados):
    tabela = tabela_frequencias(dados)
    print(f"{'Valor (xi)':^12}|{'Freq. Absoluta (fi)':^21}|{'Freq. Acumulada (Fi)':^22}")
    for xi, fi, Fi in tabela:
        print(f"{xi:^12g}|{fi:^21}|{Fi:^22}")
    m = modas_discreta(tabela)
    texto_moda = ", ".join(f"{x:.2f}" for x in m) if m else "amodal"
    print(f"Calculados via tabela: Média = {media_discreta(tabela):.2f} | "
          f"Mediana = {mediana_discreta(tabela):.2f} | Moda = {texto_moda}")

def sturges(n):
    """k = 1 + 3,322 * log10(n), arredondado."""
    return max(1, round(1 + 3.322 * math.log10(n)))

def construir_classes(dados):
    """Retorna (classes, h). Classes [li, ls); a última inclui o máximo."""
    n, mn, mx = len(dados), min(dados), max(dados)
    k = sturges(n)
    if mx == mn:
        k, h = 1, 1.0
    else:
        h = (mx - mn) / k
    freqs = [0] * k
    for v in dados:
        i = min(int((v - mn) / h + 1e-9), k - 1)
        freqs[i] += 1
    classes, acum = [], 0
    for i in range(k):
        acum += freqs[i]
        classes.append({"li": mn + i * h, "ls": mn + (i + 1) * h,
                        "fi": freqs[i], "Fi": acum})
    return classes, h

def media_classes(classes):
    n = classes[-1]["Fi"]
    return sum(c["fi"] * (c["li"] + c["ls"]) / 2 for c in classes) / n

def separatriz(classes, proporcao):
    """Mediana, quartis, decis, percentis: li + ((p*n - F_ant)/fi) * h."""
    pos = proporcao * classes[-1]["Fi"]
    for i, c in enumerate(classes):
        if c["Fi"] >= pos:
            f_ant = classes[i - 1]["Fi"] if i > 0 else 0
            return c["li"] + (pos - f_ant) / c["fi"] * (c["ls"] - c["li"])

def classe_modal(classes):
    """Classe modal (primeira em caso de empate) e fi anterior/posterior."""
    idx = max(range(len(classes)), key=lambda i: classes[i]["fi"])
    ant = classes[idx - 1]["fi"] if idx > 0 else 0
    post = classes[idx + 1]["fi"] if idx < len(classes) - 1 else 0
    return classes[idx], ant, post

def moda_czuber(classes):
    """Mo = li + d1/(d1+d2) * h."""
    c, ant, post = classe_modal(classes)
    d1, d2, h = c["fi"] - ant, c["fi"] - post, c["ls"] - c["li"]
    return c["li"] + h / 2 if d1 + d2 == 0 else c["li"] + d1 / (d1 + d2) * h

def moda_king(classes):
    """Mo = li + fpost/(fant+fpost) * h."""
    c, ant, post = classe_modal(classes)
    h = c["ls"] - c["li"]
    return c["li"] + h / 2 if ant + post == 0 else c["li"] + post / (ant + post) * h

def parte3(dados):
    classes, h = construir_classes(dados)
    print(f"n = {len(dados)} | classes (Sturges) k = {len(classes)} | amplitude h = {h:.4f}")
    print(f"{'Classe':<20}| {'fi':<5}| Fi")
    for i, c in enumerate(classes):
        fecha = "]" if i == len(classes) - 1 else ")"
        rotulo = f"[{c['li']:.2f} - {c['ls']:.2f}{fecha}"
        print(f"{rotulo:<20}| {c['fi']:<5}| {c['Fi']}")
    s = lambda p: separatriz(classes, p)
    print("Calculados via Fórmulas de Interpolação:")
    print(f"-> Média: {media_classes(classes):.2f} | Mediana: {s(.5):.2f} | "
          f"Moda (Czuber): {moda_czuber(classes):.2f} | Moda (King): {moda_king(classes):.2f}")
    print(f"-> Quartis: Q1 = {s(.25):.2f} | Q3 = {s(.75):.2f}")
    print(f"-> Decis: D2 = {s(.2):.2f} | D7 = {s(.7):.2f}")
    print("-> Percentis: " + " | ".join(f"P{p} = {s(p / 100):.2f}" for p in (15, 22, 63, 70)))

def cabecalho(titulo):
    print(f"\n{LINHA}\n{titulo}\n{LINHA}")

def main():
    print("=" * 53)
    print("   ANALISADOR ESTATÍSTICO - ENGENHARIA DE SOFTWARE")
    print("=" * 53)
    print("[1] Inserir dados via terminal (separados por vírgula)")
    print("[2] Carregar arquivo .csv\n")
    try:
        opcao = input("Escolha a opção: ").strip()
        if opcao == "1":
            dados = ler_terminal()
            print(f"Dados recebidos! (n = {len(dados)} elementos)")
        elif opcao == "2":
            dados = ler_csv(input("Caminho do arquivo .csv: ").strip())
            print(f"Arquivo carregado com sucesso! (n = {len(dados)} elementos)")
        else:
            print("Opção inválida.")
            return
    except ErroEntrada as e:
        print(f"Erro: {e}")
        return

    cabecalho("PARTE 1: DADOS NÃO AGRUPADOS (Módulo Statistics)")
    parte1(dados)
    cabecalho("PARTE 2: DISTRIBUIÇÃO DE FREQUÊNCIA (SEM INTERVALO)")
    parte2(dados)
    cabecalho("PARTE 3: DISTRIBUIÇÃO DE FREQUÊNCIA (COM INTERVALO)")
    parte3(dados)


if __name__ == "__main__":
    main()
