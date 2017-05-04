<html>
<head>
</head>
<body>
<h3>File Not Found</h3>
</body>
</html>
<?php
$ref = isset($_SERVER["HTTP_REFERER"]) ? $_SERVER["HTTP_REFERER"] : 'none';
// Since we are now running with php-fpm, we don't have access to Apache's
// errorlog, so we now send to syslog, so that we get some denoted error logged
// of 404s
openlog("dep", LOG_PID | LOG_PERROR, LOG_LOCAL1);
syslog(LOG_WARNING, "404 ". $_SERVER["REQUEST_URI"]. ' referer: '. $ref);
closelog();

?>