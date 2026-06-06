using System;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Management;
using System.ServiceProcess;
using System.Threading;

internal sealed class Options
{
    public string ServiceName = "HektorConsoleWorker";
    public string WorkerKind = "actions";
    public string ConsoleDir = AppDomain.CurrentDomain.BaseDirectory;
    public string NodeExe = "";
    public string UserProfileDir = "";
    public bool ConsoleMode = false;

    public static Options Parse(string[] args)
    {
        var options = new Options();
        for (var i = 0; i < args.Length; i++)
        {
            var arg = args[i];
            if (arg == "--console")
            {
                options.ConsoleMode = true;
                continue;
            }
            if (i + 1 >= args.Length)
            {
                continue;
            }
            var value = args[++i];
            switch (arg)
            {
                case "--service-name":
                    options.ServiceName = value;
                    break;
                case "--worker-kind":
                    options.WorkerKind = value;
                    break;
                case "--console-dir":
                    options.ConsoleDir = value;
                    break;
                case "--node-exe":
                    options.NodeExe = value;
                    break;
                case "--user-profile-dir":
                    options.UserProfileDir = value;
                    break;
            }
        }
        return options;
    }
}

internal sealed class HektorWorkerService : ServiceBase
{
    private readonly Options _options;
    private readonly object _sync = new object();
    private Process _process;
    private bool _stopping;
    private string _logPath;

    public HektorWorkerService(Options options)
    {
        _options = options;
        ServiceName = options.ServiceName;
        CanStop = true;
        CanShutdown = true;
    }

    public void RunConsole()
    {
        OnStart(new string[0]);
        Console.WriteLine("Service wrapper running in console mode. Press Ctrl+C to stop.");
        using (var wait = new ManualResetEvent(false))
        {
            Console.CancelKeyPress += (sender, eventArgs) =>
            {
                eventArgs.Cancel = true;
                OnStop();
                wait.Set();
            };
            wait.WaitOne();
        }
    }

    protected override void OnStart(string[] args)
    {
        Directory.CreateDirectory(LogDir);
        _logPath = Path.Combine(LogDir, "console_worker_service_" + _options.WorkerKind + ".log");
        Log("service starting");
        StartWorker();
    }

    protected override void OnStop()
    {
        _stopping = true;
        Log("service stopping");
        StopWorker();
    }

    protected override void OnShutdown()
    {
        OnStop();
    }

    private string LogDir
    {
        get { return Path.Combine(_options.ConsoleDir, "logs"); }
    }

    private string SessionsDir
    {
        get { return Path.Combine(_options.ConsoleDir, "sessions"); }
    }

    private void StartWorker()
    {
        lock (_sync)
        {
            if (_stopping)
            {
                return;
            }
            if (_process != null && !_process.HasExited)
            {
                return;
            }

            Directory.CreateDirectory(SessionsDir);
            var nodeExe = ResolveNodeExe();
            var scriptPath = Path.Combine(_options.ConsoleDir, "console_job_worker.js");
            var psi = new ProcessStartInfo
            {
                FileName = nodeExe,
                Arguments = Quote(scriptPath),
                WorkingDirectory = _options.ConsoleDir,
                UseShellExecute = false,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                CreateNoWindow = true
            };
            ConfigureEnvironment(psi);

            var process = new Process { StartInfo = psi, EnableRaisingEvents = true };
            process.OutputDataReceived += (sender, eventArgs) => { if (eventArgs.Data != null) Log(eventArgs.Data); };
            process.ErrorDataReceived += (sender, eventArgs) => { if (eventArgs.Data != null) Log("ERR " + eventArgs.Data); };
            process.Exited += WorkerExited;
            process.Start();
            process.BeginOutputReadLine();
            process.BeginErrorReadLine();
            _process = process;
            Log("worker started pid=" + process.Id + " kind=" + _options.WorkerKind);
        }
    }

    private void WorkerExited(object sender, EventArgs eventArgs)
    {
        var exitCode = -1;
        try
        {
            exitCode = ((Process)sender).ExitCode;
        }
        catch
        {
        }
        Log("worker exited code=" + exitCode);
        if (_stopping)
        {
            return;
        }
        ThreadPool.QueueUserWorkItem(_ =>
        {
            Thread.Sleep(TimeSpan.FromSeconds(10));
            StartWorker();
        });
    }

    private void StopWorker()
    {
        Process process;
        lock (_sync)
        {
            process = _process;
            _process = null;
        }
        if (process == null)
        {
            return;
        }
        try
        {
            if (!process.HasExited)
            {
                KillProcessTree(process.Id);
            }
        }
        catch (Exception ex)
        {
            Log("stop error " + ex.GetType().Name + ": " + ex.Message);
        }
    }

    private void ConfigureEnvironment(ProcessStartInfo psi)
    {
        var kind = _options.WorkerKind;
        psi.EnvironmentVariables["CONSOLE_WORKER_ENABLE_HEKTOR_ACTIONS"] = "true";
        psi.EnvironmentVariables["CONSOLE_WORKER_ENABLE_MATTERPORT_ACTIONS"] = "true";
        psi.EnvironmentVariables["CONSOLE_WORKER_KIND"] = kind;
        psi.EnvironmentVariables["CONSOLE_WORKER_GENERATION"] = "v9";
        psi.EnvironmentVariables["CONSOLE_WORKER_ID"] = Environment.MachineName + ":" + kind + ":service:v9";
        psi.EnvironmentVariables["CONSOLE_WORKER_POLL_INTERVAL_MS"] = kind == "sync_light" ? "10000" : "5000";
        psi.EnvironmentVariables["CONSOLE_HEKTOR_SESSION_REFRESH_MS"] = "7200000";
        psi.EnvironmentVariables["CONSOLE_HEKTOR_CONTEXT_SWITCH_FALLBACK_PLAYWRIGHT"] = "true";
        psi.EnvironmentVariables["CONSOLE_HEKTOR_ALLOW_UNVERIFIED_CONTEXT"] = "true";
        psi.EnvironmentVariables["CONSOLE_HEKTOR_HEADLESS"] = "true";
        psi.EnvironmentVariables["CONSOLE_LOCAL_ARCHIVE_ROOT"] = @"C:\Hektor\HektorConsoleDocuments";
        psi.EnvironmentVariables["CONSOLE_STORAGE_STATE_PATH"] = Path.Combine(SessionsDir, "storage_state_" + kind + ".json");
        psi.EnvironmentVariables["MATTERPORT_STORAGE_STATE_PATH"] = Path.Combine(_options.ConsoleDir, "matterport_storage_state.json");

        if (!string.IsNullOrWhiteSpace(_options.UserProfileDir) && Directory.Exists(_options.UserProfileDir))
        {
            var appData = Path.Combine(_options.UserProfileDir, "AppData", "Roaming");
            var localAppData = Path.Combine(_options.UserProfileDir, "AppData", "Local");
            psi.EnvironmentVariables["USERPROFILE"] = _options.UserProfileDir;
            psi.EnvironmentVariables["APPDATA"] = appData;
            psi.EnvironmentVariables["LOCALAPPDATA"] = localAppData;
            var browsersPath = Path.Combine(localAppData, "ms-playwright");
            if (Directory.Exists(browsersPath))
            {
                psi.EnvironmentVariables["PLAYWRIGHT_BROWSERS_PATH"] = browsersPath;
            }
        }
    }

    private string ResolveNodeExe()
    {
        if (!string.IsNullOrWhiteSpace(_options.NodeExe) && File.Exists(_options.NodeExe))
        {
            return _options.NodeExe;
        }
        var candidates = new[]
        {
            Environment.GetEnvironmentVariable("CONSOLE_NODE_EXE"),
            Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ProgramFiles), "nodejs", "node.exe"),
            "node.exe"
        };
        return candidates.FirstOrDefault(candidate => !string.IsNullOrWhiteSpace(candidate) && (candidate == "node.exe" || File.Exists(candidate))) ?? "node.exe";
    }

    private static void KillProcessTree(int pid)
    {
        using (var searcher = new ManagementObjectSearcher("Select * From Win32_Process Where ParentProcessID=" + pid))
        using (var children = searcher.Get())
        {
            foreach (ManagementObject child in children)
            {
                KillProcessTree(Convert.ToInt32(child["ProcessID"]));
            }
        }
        try
        {
            var process = Process.GetProcessById(pid);
            if (!process.HasExited)
            {
                process.Kill();
                process.WaitForExit(10000);
            }
        }
        catch
        {
        }
    }

    private void Log(string message)
    {
        try
        {
            File.AppendAllText(_logPath, DateTimeOffset.Now.ToString("o") + " " + message + Environment.NewLine);
        }
        catch
        {
        }
    }

    private static string Quote(string value)
    {
        return "\"" + value.Replace("\"", "\\\"") + "\"";
    }
}

internal static class Program
{
    private static int Main(string[] args)
    {
        var options = Options.Parse(args);
        var service = new HektorWorkerService(options);
        if (options.ConsoleMode || Environment.UserInteractive)
        {
            service.RunConsole();
            return 0;
        }
        ServiceBase.Run(service);
        return 0;
    }
}
