<?php
// CEL PARK — backend formularza (PHP mail). Wymaga hostingu z PHP >= 7.4 i skonfigurowaną funkcją mail()/SMTP.
header('Content-Type: application/json; charset=utf-8');
if ($_SERVER['REQUEST_METHOD'] !== 'POST') { http_response_code(405); echo json_encode(['ok' => false, 'error' => 'method']); exit; }
if (!empty($_POST['website'])) { echo json_encode(['ok' => true]); exit; } // honeypot
$name = trim(strip_tags($_POST['name'] ?? '')); $email = trim($_POST['email'] ?? ''); $phone = trim(strip_tags($_POST['phone'] ?? ''));
$unit = trim(strip_tags($_POST['unit'] ?? '')); $mode = trim(strip_tags($_POST['mode'] ?? '')); $msg = trim(strip_tags($_POST['msg'] ?? ''));
if ($name === '' || !filter_var($email, FILTER_VALIDATE_EMAIL)) { http_response_code(400); echo json_encode(['ok' => false, 'error' => 'invalid']); exit; }
$to = 'sprzedaz@celpark.pl';
$subject = '=?UTF-8?B?' . base64_encode("CEL PARK Dąbrówka.01 – zapytanie o lokal $unit ($mode)") . '?=';
$body = "Imię i nazwisko: $name\nTelefon: " . ($phone ?: '-') . "\nE-mail: $email\nLokal: $unit\nInteresuje mnie: $mode\n\n$msg\n\n— wysłano ze strony celpark.pl, " . date('Y-m-d H:i') . ", IP " . ($_SERVER['REMOTE_ADDR'] ?? '');
$headers = "From: CEL PARK <formularz@celpark.pl>\r\nReply-To: $email\r\nContent-Type: text/plain; charset=UTF-8\r\nX-Mailer: celpark-form";
$ok = @mail($to, $subject, $body, $headers);
echo json_encode(['ok' => (bool)$ok]);
