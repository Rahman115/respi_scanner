<?php

declare(strict_types=1);

require_once __DIR__ . '/BaseController.php';

class DashboardController extends BaseController
{
    public function index(): void
    {
        $this->view('dashboard/index', ['title' => 'Dashboard']);
    }
}
