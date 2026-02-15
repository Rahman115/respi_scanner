<!doctype html>
<html lang="id">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title><?= htmlspecialchars($title ?? 'Absensi MVC', ENT_QUOTES, 'UTF-8') ?></title>
</head>
<body>
    <main>
        <?= $content ?? '' ?>
    </main>
</body>
</html>
