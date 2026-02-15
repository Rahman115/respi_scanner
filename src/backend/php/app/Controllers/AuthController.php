<?php

declare(strict_types=1);

require_once __DIR__ . '/BaseController.php';

class AuthController extends BaseController
{
    public function showLogin(): void
    {
        $this->view('auth/login', ['title' => 'Login']);
    }
}
