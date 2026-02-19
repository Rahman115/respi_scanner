<?php

declare(strict_types=1);

require_once __DIR__ . '/Router.php';
require_once __DIR__ . '/../Controllers/AuthController.php';
require_once __DIR__ . '/../Controllers/DashboardController.php';

class App
{
    public function run(): void
    {
        $router = new Router();

        $router->get('/', [DashboardController::class, 'index']);
        $router->get('/login', [AuthController::class, 'showLogin']);

        $router->dispatch($_SERVER['REQUEST_METHOD'] ?? 'GET', $_SERVER['REQUEST_URI'] ?? '/');
    }
}
