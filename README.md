# Kickbase Lister

Ein sehr simples Tool um ein paar Stats zu berechnen, die nicht in der Kickbase APP angezeigt werden, mehr oder weniger schön formatiert in einer HTML Tabelle. Fast der gesamte Code wurde von [Kickbase-Insights](https://github.com/casudo/Kickbase-Insights) adaptiert, danke [Casudo](https://github.com/casudo). Auch ist die [kickbase api documentation](https://github.com/kevinskyba/kickbase-api-doc) sehr hilfreich gewesen.


## Installation
Nachdem die erforderlichen Packages mit ```pip install -r requirements.txt``` installiert wurden, muss eine ```.env``` Datei wie die Beispieldatei ```env.example``` mit Email und Passwort des Kickbase accounts erstellt werden. Dann reicht das ausführen von ```user_list.py```.

### TODOs
Geplant war eine Punktevorhersage basierend auf den durchschnittlichen Punkten pro Minuten von allen Spielern, dazu sind ```graph.py``` und ```player_analyze.py``` gedacht. Außerdem ist es relativ einfach mit den bereits geschriebenen Funktionen das Cash, was jeder Manager zu Verfügung hat, auszurechnen.

### Beispiel
<head>
 <style>
  body {
        font-family: Arial, sans-serif;
    }
    table {
        width: 100%;
        border-collapse: collapse; /* Removes space between cell borders */
        margin: 20px 0;
    }
    th, td {
        border: 1px solid #444444; /* Darker border for the theme */
        padding: 12px;
        text-align: left;
    }
    th {
        background-color: #333333; /* Header background */
    }
    /* Zebra-striping for data rows */
    tbody tr:nth-child(even) {
        background-color: #222222;
    }
    tbody tr:hover {
        background-color: #444444; /* Highlight row on hover */
    }
    /* Center the text in these specific columns */
    .center-text {
        text-align: center;
    }
 </style>
</head>
<table>
 <thead>
  <tr>
   <th>
    Name
   </th>
   <th>
    Teamwert
   </th>
   <th class="center-text" style="text-align: center;">
    Gesamtpunkte
   </th>
   <th class="center-text" style="text-align: center;">
    Matchday-Siege
   </th>
   <th class="center-text">
    Big Boy
   </th>
   <th class="center-text" style="text-align: center;">
    500k Spieler
   </th>
   <th>
    Größter overpay Spieler
   </th>
   <th>
    Größter Verlust Spieler
   </th>
   <th>
    Größter Gewinn Spieler
   </th>
  </tr>
 </thead>
 <tbody>
  <tr>
   <td>
    <div style="display: flex; align-items: center; justify-content: center; gap: 10px;">
     <span>
      Testuser
     </span>
    </div>
   </td>
   <td>
    169.7M (67.6M⬆️)
   </td>
   <td class="center-text" style="text-align: center;">
    123
   </td>
   <td class="center-text" style="text-align: center;">
    2
   </td>
   <td class="center-text">
    Tah (44.0M)
   </td>
   <td class="center-text" style="text-align: center;">
    3
   </td>
   <td>
    Tah (4.1M)
   </td>
   <td>
    Theate (-236.6K)
   </td>
   <td>
    Heuer Fernandes (760.7K)
   </td>
  </tr>

 </tbody>
</table>
