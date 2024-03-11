# CarsProject

Voici les étapes à suivre pour créer un environnement virtuel Python 3.11.5 dans Visual Studio Code en utilisant le chemin d'accès complet à l'exécutable Python :

Ouvrez une nouvelle fenêtre de terminal dans Visual Studio Code en cliquant sur "Terminal" -> "Nouveau terminal" dans la barre de menu.
Dans le terminal, accédez au répertoire de votre projet en utilisant la commande cd. Par exemple, si votre projet se trouve dans le répertoire C:\Users\yzi\Desktop\Travaux\CarsProject, vous devez entrer la commande suivante :

Découvrez le chemin d'accès complet à l'exécutable Python 3.11.5 en utilisant la commande where python. Cela devrait afficher une liste des emplacements où Python est installé sur votre système. Recherchez l'emplacement où Python 3.11.5 est installé. Le chemin d'accès complet devrait ressembler à ceci :

`C:\Users\votre_nom_utilisateur\AppData\Local\Programs\Python\Python311\python.exe`
Créez un environnement virtuel en utilisant le chemin d'accès complet à l'exécutable Python 3.11.5. Par exemple, si vous voulez créer un environnement virtuel nommé "dev_env3.11.5", vous devez entrer la commande suivante :

`C:\Users\votre_nom_utilisateur\AppData\Local\Programs\Python\Python311\python.exe -m venv dev_env3.11.5`
N'oubliez pas de remplacer "votre_nom_utilisateur" par votre propre nom d'utilisateur Windows.

Activez l'environnement virtuel en utilisant la commande suivante :

`.\dev_env3.11.5\Scripts\activate`
Vous devriez maintenant voir le nom de l'environnement virtuel dans l'invite de commande, ce qui indique que vous êtes maintenant dans l'environnement virtuel.

Vous pouvez maintenant installer les packages Python dont vous avez besoin en utilisant pip install. Par exemple, pour installer le package "requests", entrez la commande suivante :

pip install requests
Créez un nouveau fichier Python dans votre dossier de projet et commencez à coder !
Vous avez maintenant un environnement de développement Python 3.11.5 configuré dans Visual Studio Code.