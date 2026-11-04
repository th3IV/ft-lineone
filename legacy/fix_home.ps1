$path = "D:\ft-lineone\frontend\src\pages\Home.jsx"
$lines = Get-Content $path
$lines[54] = '                className={${store.color} text-white px-6 py-3 rounded-lg font-medium hover:opacity-90 transition-opacity}'
$lines[55] = '              >'
$lines[56] = '                {store.name}'
$lines[57] = '              </Link>'
$lines | Set-Content $path
