const {
  useState,
  useEffect,
  useRef
} = React;
function App() {
  const [view, setView] = useState('main'); // 'main' | 'archive' | 'sources' | 'digest' | 'admin'

  // ================= 0. АВТОРИЗАЦИЯ (Telegram WebApp initData + FaceID) =================
  const [auth, setAuth] = useState({
    state: 'loading',
    user: null
  }); // loading | login | ok
  const [authError, setAuthError] = useState('');
  const [bioStatus, setBioStatus] = useState(''); // диагностика FaceID: что происходит

  // обёртка fetch: добавляет Authorization: Bearer <token>
  const apiFetch = (url, opts = {}) => {
    const token = sessionStorage.getItem('hub_token');
    const headers = {
      ...(opts.headers || {})
    };
    if (token) headers['Authorization'] = 'Bearer ' + token;
    return fetch(url, {
      ...opts,
      headers
    });
  };

  // при старте: проверить токен + заранее инициализировать биометрию
  useEffect(() => {
    const token = sessionStorage.getItem('hub_token');
    if (!token) {
      setAuth({
        state: 'login',
        user: null
      });
    } else {
      // SWR: сначала показываем кеш из localStorage (мгновенный старт),
      // затем один /api/bootstrap обновляет всё разом
      try {
        const cached = localStorage.getItem('hub_bootstrap_v1');
        if (cached) {
          const c = JSON.parse(cached);
          if (c.user) setAuth({
            state: 'ok',
            user: c.user
          });
          if (c.sources) setSources(c.sources);
          if (c.digest) setDigestData(c.digest);
          if (c.calendar) setCalendarData(c.calendar);
        }
      } catch {}
      apiFetch('/miniapp/api/bootstrap').then(r => r.ok ? r.json() : Promise.reject()).then(d => {
        setAuth({
          state: 'ok',
          user: d.user
        });
        if (d.sources) setSources(d.sources);
        if (d.digest) setDigestData(d.digest);
        if (d.calendar) setCalendarData(d.calendar);
        try {
          localStorage.setItem('hub_bootstrap_v1', JSON.stringify({
            user: d.user,
            sources: d.sources,
            digest: d.digest,
            calendar: d.calendar,
            ts: Date.now()
          }));
        } catch {}
      }).catch(() => {
        sessionStorage.removeItem('hub_token');
        setAuth({
          state: 'login',
          user: null
        });
      });
    }
    // заранее инициализируем BiometricManager, чтобы к моменту клика он был готов
    const tg = window.Telegram?.WebApp;
    const bm = tg?.BiometricManager;
    if (tg && !tg.initData) setBioStatus('⚠ нет initData (открыто не из Telegram?)');
    if (bm && !bm.isInited) {
      setBioStatus('⏳ инициализация биометрии…');
      bm.init(() => {
        setBioStatus(bm.isBiometricAvailable ? `✅ биометрия доступна (тип: ${bm.biometricType || '?'}${bm.isAccessGranted ? ', доступ ✓' : ', доступ не выдан'})` : '❌ биометрия НЕдоступна на этом устройстве');
      });
    } else if (bm) {
      setBioStatus(bm.isBiometricAvailable ? `✅ биометрия доступна (тип: ${bm.biometricType || '?'}${bm.isAccessGranted ? ', доступ ✓' : ', доступ не выдан'})` : '❌ биометрия НЕдоступна на этом устройстве');
    } else {
      setBioStatus('— BiometricManager не найден (старый клиент?)');
    }
  }, []);
  const doLogin = () => {
    setAuthError('');
    const tg = window.Telegram?.WebApp;
    const bm = tg?.BiometricManager;
    const attempt = () => {
      const initData = tg?.initData || '';
      fetch('/miniapp/api/auth', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          initData
        })
      }).then(r => r.json()).then(d => {
        if (d.token) {
          sessionStorage.setItem('hub_token', d.token);
          setAuth({
            state: 'ok',
            user: d.user
          });
        } else {
          setAuthError(d.error || 'Ошибка входа');
        }
      }).catch(() => setAuthError('Сервер недоступен'));
    };
    const authFace = () => {
      // на десктопе (Telegram Desktop/Mac) биометрия часто недоступна —
      // не идём в requestAccess, сразу вход по подписи Telegram
      if (!bm.isBiometricAvailable) {
        setBioStatus('— биометрия недоступна на этом устройстве, вход по подписи Telegram');
        attempt();
        return;
      }
      setBioStatus('🔄 запрашиваем FaceID…');
      const faceDone = label => {
        // Флаг isAuthenticated на iOS обновляется асинхронно/глючит —
        // проверяем с задержкой, но НЕ блокируем вход: initData уже
        // проверен сервером криптографически, FaceID — UX-подтверждение.
        setTimeout(() => {
          setBioStatus(bm.isAuthenticated ? '✅ FaceID подтверждён' : label + ' (флаг клиента не обновился, вход по подписи Telegram)');
          attempt();
        }, 200);
      };
      try {
        // новые версии API: requestAccess({reason}, cb)
        bm.requestAccess({
          reason: 'Вход в Personal Hub'
        }, () => {
          setBioStatus(bm.isAccessGranted ? '✅ доступ к биометрии выдан, сканируем…' : '⚠ доступ к биометрии не выдан — вход без FaceID');
          if (bm.isAccessGranted) {
            bm.authenticate({
              reason: 'Вход в Personal Hub'
            }, () => {
              faceDone('✅ FaceID: лицо принято');
            });
          } else {
            attempt();
          }
        });
      } catch (e) {
        // старые версии API: requestAccess(cb), authenticate(cb)
        setBioStatus('⚠ старый API биометрии');
        bm.requestAccess(() => {
          if (bm.isAccessGranted) {
            bm.authenticate('Вход в Personal Hub', () => {
              faceDone('✅ FaceID: лицо принято');
            });
          } else attempt();
        });
      }
    };
    // сначала FaceID (если доступен), затем initData
    if (bm) {
      if (bm.isInited) {
        authFace();
      } else {
        setBioStatus('⏳ инициализация биометрии…');
        // на десктопе init может не вызвать колбэк — страховка: таймаут
        let done = false;
        const fallback = () => {
          if (done) return;
          done = true;
          setBioStatus('— биометрия не ответила, вход по подписи Telegram');
          attempt();
        };
        setTimeout(fallback, 2500);
        try {
          bm.init(() => {
            if (done) return;
            done = true;
            authFace();
          });
        } catch (e) {
          fallback();
        }
      }
    } else {
      setBioStatus('— биометрия недоступна, вход по подписи Telegram');
      attempt();
    }
    haptic && haptic('medium');
  };
  const doLogout = () => {
    const token = sessionStorage.getItem('hub_token');
    if (token) apiFetch('/miniapp/api/auth/logout', {
      method: 'POST'
    }).catch(() => {});
    sessionStorage.removeItem('hub_token');
    setAuth({
      state: 'login',
      user: null
    });
  };

  // ================= ПАРОЛЬ (для входа на десктопе/браузере) =================
  const [passState, setPassState] = useState({
    showSet: false,
    showLogin: false,
    newPass: '',
    login: '',
    pwd: '',
    setPwd: '',
    msg: ''
  });
  const setMyPassword = () => {
    const p = passState.newPass;
    if (p.length < 4) {
      setPassState(s => ({
        ...s,
        msg: 'Пароль слишком короткий (мин. 4)'
      }));
      return;
    }
    apiFetch('/miniapp/api/auth', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        setPassword: true,
        password: p
      })
    }).then(r => r.json()).then(d => {
      setPassState(s => ({
        ...s,
        msg: d.ok ? '✅ Пароль сохранён' : d.error || 'Ошибка',
        newPass: d.ok ? '' : s.newPass
      }));
    }).catch(() => setPassState(s => ({
      ...s,
      msg: 'Сервер недоступен'
    })));
    haptic('light');
  };
  // установка пароля прямо с экрана входа (по initData, работает и на Mac в Telegram)
  const setPasswordOnLogin = () => {
    const p = passState.setPwd;
    if (p.length < 4) {
      setPassState(s => ({
        ...s,
        msg: 'Пароль слишком короткий (мин. 4)'
      }));
      return;
    }
    setPassState(s => ({
      ...s,
      msg: ''
    }));
    fetch('/miniapp/api/auth', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        setPassword: true,
        password: p,
        initData: window.Telegram?.WebApp?.initData || ''
      })
    }).then(r => r.json()).then(d => {
      setPassState(s => ({
        ...s,
        msg: d.ok ? '✅ Пароль сохранён! Теперь войдите по нему' : d.error || 'Ошибка',
        setPwd: d.ok ? '' : s.setPwd
      }));
    }).catch(() => setPassState(s => ({
      ...s,
      msg: 'Сервер недоступен'
    })));
    haptic('light');
  };
  const doLoginPassword = () => {
    const {
      login,
      pwd
    } = passState;
    if (!login || !pwd) {
      setPassState(s => ({
        ...s,
        msg: 'Введите логин и пароль'
      }));
      return;
    }
    setPassState(s => ({
      ...s,
      msg: ''
    }));
    fetch('/miniapp/api/auth', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        username: login,
        password: pwd
      })
    }).then(r => r.json()).then(d => {
      if (d.token) {
        sessionStorage.setItem('hub_token', d.token);
        setAuth({
          state: 'ok',
          user: d.user
        });
      } else {
        setPassState(s => ({
          ...s,
          msg: d.error || 'Ошибка входа'
        }));
      }
    }).catch(() => setPassState(s => ({
      ...s,
      msg: 'Сервер недоступен'
    })));
    haptic('medium');
  };

  // ================= 1. ПОГОДА =================
  const [weather, setWeather] = useState({
    temp: 24,
    condition: 'Ясно, без осадков',
    wind: '2.8 м/с',
    city: 'Москва',
    icon: 'clear-day'
  });
  const [om, setOm] = useState(null); // Open-Meteo: текущие + почасовой прогноз (Москва)
  const [hourOffset, setHourOffset] = useState(0); // прокрутка прогноза: +0..12 ч

  // Текущая погода + почасовой прогноз по Москве (Open-Meteo, без ключей)
  useEffect(() => {
    fetch('https://api.open-meteo.com/v1/forecast?latitude=55.7558&longitude=37.6173&hourly=temperature_2m,rain,snowfall,wind_speed_10m,weathercode&current=temperature_2m,rain,snowfall,wind_speed_10m,weathercode&timezone=Europe%2FMoscow&forecast_days=2').then(r => r.json()).then(d => setOm(d)).catch(() => {});
  }, []);

  // ================= 2. ЗАДАЧИ & АРХИВ =================
  const [tasks, setTasks] = useState(() => {
    try {
      const saved = localStorage.getItem('hub_tasks_v2');
      return saved ? JSON.parse(saved) : [{
        id: 1,
        text: 'Согласовать спецификацию с юристами',
        done: false,
        createdAt: '10:15'
      }, {
        id: 2,
        text: 'Проверить выгрузку реестра оплат',
        done: true,
        createdAt: 'Вчера, 18:30'
      }];
    } catch {
      return [];
    }
  });
  const [taskInput, setTaskInput] = useState('');
  useEffect(() => {
    localStorage.setItem('hub_tasks_v2', JSON.stringify(tasks));
  }, [tasks]);
  const handleAddTask = textOverride => {
    const text = (textOverride || taskInput).trim();
    if (!text) return;
    const now = new Date();
    const timeStr = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;
    const dateStr = now.toLocaleDateString('ru-RU', {
      day: '2-digit',
      month: '2-digit'
    });
    const newTask = {
      id: Date.now(),
      text: text,
      done: false,
      createdAt: `${dateStr}, ${timeStr}`
    };
    setTasks(prev => [newTask, ...prev]);
    setTaskInput('');
    haptic('medium');
  };

  // Голосовой ввод задачи (Web Speech API, где поддерживается)
  const [voiceError, setVoiceError] = useState('');
  const startVoiceInput = () => {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) {
      setVoiceError('Голосовой ввод не поддерживается в этом браузере');
      setTimeout(() => setVoiceError(''), 3000);
      return;
    }
    setVoiceError('');
    const rec = new SR();
    rec.lang = 'ru-RU';
    rec.interimResults = false;
    rec.maxAlternatives = 1;
    rec.onresult = e => {
      const text = e.results[0][0].transcript;
      // сначала — в поле ввода, пользователь сам жмёт «+» для добавления
      setTaskInput(text);
    };
    rec.onerror = () => {
      setVoiceError('Не удалось распознать речь, попробуйте ещё раз');
      setTimeout(() => setVoiceError(''), 3000);
    };
    rec.start();
    haptic('medium');
  };
  const toggleTask = id => {
    haptic('light');
    setTasks(prev => prev.map(t => {
      if (t.id === id) {
        return {
          ...t,
          done: !t.done
        };
      }
      return t;
    }));
  };
  const deleteTask = id => {
    haptic('light');
    setTasks(prev => prev.filter(t => t.id !== id));
  };
  const clearArchive = () => {
    haptic('heavy');
    setTasks(prev => prev.filter(t => !t.done));
  };
  const activeTasks = tasks.filter(t => !t.done);
  const completedTasks = tasks.filter(t => t.done);

  // ================= 3. ИСТОЧНИКИ & RSS (через серверный API) =================
  const [sources, setSources] = useState([]);
  const [sourceName, setSourceName] = useState('');
  const [sourceType, setSourceType] = useState('TG');
  const [sourceError, setSourceError] = useState('');
  const loadSources = () => {
    apiFetch('/miniapp/api/sources').then(r => r.json()).then(d => {
      if (d?.sources) setSources(d.sources);
    }).catch(() => {});
  };
  useEffect(() => {
    if (auth.state === 'ok' && !sources.length) loadSources();
  }, [auth.state]);
  const handleAddSource = async () => {
    const val = sourceName.trim();
    if (!val) return;
    setSourceError('');
    try {
      const r = await apiFetch('/miniapp/api/sources', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          type: sourceType,
          name: val,
          title: val
        })
      });
      const d = await r.json();
      if (d?.sources) setSources(d.sources);
      setSourceName('');
      setView('sources');
      haptic('medium');
    } catch {
      setSourceError('Не удалось добавить источник');
    }
  };
  const deleteSource = async id => {
    haptic('light');
    try {
      const r = await apiFetch('/miniapp/api/sources?id=' + id, {
        method: 'DELETE'
      });
      const d = await r.json();
      if (d?.sources) setSources(d.sources);
    } catch {}
  };

  // ================= 4. ДАЙДЖЕСТ (живой, через API) =================
  const [digestData, setDigestData] = useState(null);
  const [digestLoading, setDigestLoading] = useState(false);
  const [digestError, setDigestError] = useState('');
  const [openPosts, setOpenPosts] = useState({}); // какие блоки дайджеста развёрнуты

  // ================= 4.5. GOOGLE КАЛЕНДАРЬ (через /api/calendar) =================
  const [calendarData, setCalendarData] = useState(null);
  const [calendarError, setCalendarError] = useState('');

  // календарь приходит в /api/bootstrap; фолбэк — если нужен свежий
  useEffect(() => {
    if (auth.state !== 'ok' || calendarData) return;
    apiFetch('/miniapp/api/calendar').then(r => r.json()).then(d => setCalendarData(d)).catch(() => setCalendarError('Календарь недоступен'));
  }, [auth.state]);
  const loadDigest = () => {
    setDigestLoading(true);
    setDigestError('');
    apiFetch('/miniapp/api/digest').then(r => r.json()).then(d => setDigestData(d)).catch(() => setDigestError('Не удалось загрузить дайджест')).finally(() => setDigestLoading(false));
  };
  useEffect(() => {
    if (view === 'digest') loadDigest();
  }, [view]);

  // ================= 5. ВАЛЮТЫ & ПАРОЛИ =================
  const [rates, setRates] = useState({
    USD: 91.20,
    EUR: 98.40,
    CNY: 12.65,
    JPY: 0.62,
    GBP: 116.50,
    RUB: 1.00
  });
  const [calcAmount, setCalcAmount] = useState(1000);
  const [fromCurr, setFromCurr] = useState('CNY');
  const [toCurr, setToCurr] = useState('RUB');
  const [showRates, setShowRates] = useState(false); // конвертер валют: развернуть по клику на значок
  const [showPass, setShowPass] = useState(false); // генератор паролей: развернуть по клику на значок
  const [showFeed, setShowFeed] = useState(false); // лента каналов & RSS: развернуть по клику на значок

  const [passLength, setPassLength] = useState(16);
  const [password, setPassword] = useState('k9#vL@8$qP2!mZ7x');
  const [copied, setCopied] = useState(false);
  useEffect(() => {
    if (window.Telegram?.WebApp) {
      window.Telegram.WebApp.ready();
      window.Telegram.WebApp.expand();
    }
    fetch('https://www.cbr-xml-daily.ru/daily_json.js').then(r => r.json()).then(d => {
      if (d?.Valute) {
        setRates({
          USD: d.Valute.USD.Value,
          EUR: d.Valute.EUR.Value,
          CNY: d.Valute.CNY.Value,
          JPY: d.Valute.JPY.Value / d.Valute.JPY.Nominal,
          GBP: d.Valute.GBP.Value,
          RUB: 1.00
        });
      }
    }).catch(() => {});
    // Реальная погода для Москвы (Open-Meteo, без ключа)
    fetch('https://api.open-meteo.com/v1/forecast?latitude=55.7558&longitude=37.6173&current_weather=true&timezone=Europe%2FMoscow').then(r => r.json()).then(d => {
      const cw = d?.current_weather;
      if (!cw) return;
      const codes = {
        0: ['Ясно', 'clear-day'],
        1: ['Почти ясно', 'partly-cloudy-day'],
        2: ['Переменная облачность', 'partly-cloudy-day'],
        3: ['Пасмурно', 'overcast'],
        45: ['Туман', 'fog'],
        48: ['Изморозь', 'fog'],
        51: ['Морось', 'drizzle'],
        53: ['Морось', 'drizzle'],
        55: ['Морось', 'drizzle'],
        61: ['Небольшой дождь', 'rain'],
        63: ['Дождь', 'rain'],
        65: ['Сильный дождь', 'rain'],
        71: ['Небольшой снег', 'snow'],
        73: ['Снег', 'snow'],
        75: ['Сильный снег', 'snow'],
        80: ['Ливень', 'rain'],
        81: ['Ливень', 'rain'],
        82: ['Сильный ливень', 'thunderstorms'],
        95: ['Гроза', 'thunderstorms'],
        96: ['Гроза с градом', 'thunderstorms'],
        99: ['Гроза с градом', 'thunderstorms']
      };
      const c = codes[cw.weathercode];
      setWeather({
        temp: Math.round(cw.temperature),
        condition: c ? c[0] : 'Код ' + cw.weathercode,
        icon: c ? c[1] : 'cloudy',
        wind: cw.windspeed + ' м/с',
        city: 'Москва'
      });
    }).catch(() => {});
  }, []);
  const haptic = (type = 'light') => {
    window.Telegram?.WebApp?.HapticFeedback?.impactOccurred(type);
  };

  // день/ночь для фона погодной карточки (21:00–06:00 — ночь, ?night=1 — принудительно)
  const isNightTime = () => {
    if (location.search.includes('night=1')) return true;
    const h = new Date().getHours();
    return h >= 21 || h < 6;
  };
  const convertValue = () => {
    const inRub = calcAmount * rates[fromCurr];
    const res = inRub / rates[toCurr];
    return res.toLocaleString('ru-RU', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    });
  };
  const generatePassword = () => {
    haptic('light');
    const chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+~';
    let res = '';
    for (let i = 0; i < passLength; i++) {
      res += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    setPassword(res);
    setCopied(false);
  };
  const copyToClipboard = () => {
    navigator.clipboard.writeText(password);
    setCopied(true);
    haptic('notification');
    setTimeout(() => setCopied(false), 2000);
  };

  // ================= 6. ВИКТОРИНЫ (Open Trivia DB) & ИДЕИ (BoredAPI) =================
  const [quiz, setQuiz] = useState(null);
  const [quizLoading, setQuizLoading] = useState(false);
  const [quizError, setQuizError] = useState('');
  const [showAnswer, setShowAnswer] = useState(false);
  const [activity, setActivity] = useState(null);
  const [activityLoading, setActivityLoading] = useState(false);
  const [activityError, setActivityError] = useState('');
  const loadQuiz = () => {
    setQuizLoading(true);
    setQuizError('');
    setShowAnswer(false);
    apiFetch('/miniapp/api/quiz?count=1').then(r => r.json()).then(d => {
      if (d.ok && d.clues && d.clues.length) setQuiz(d.clues[0]);else setQuizError(d.error || 'Не удалось получить вопрос');
    }).catch(() => setQuizError('Сервер недоступен')).finally(() => setQuizLoading(false));
  };
  const loadActivity = () => {
    setActivityLoading(true);
    setActivityError('');
    apiFetch('/miniapp/api/activity').then(r => r.json()).then(d => {
      if (d.ok && d.activity && d.activity.activity) setActivity(d.activity);else setActivityError(d.error || 'Не удалось получить идею');
    }).catch(() => setActivityError('Сервер недоступен')).finally(() => setActivityLoading(false));
  };
  useEffect(() => {
    if (view === 'fun') {
      if (!quiz) loadQuiz();
      if (!activity) loadActivity();
    }
  }, [view]);

  // ================= 7. ПЕРЕВОДЧИК (MyMemory через /api/translate) =================
  const [trText, setTrText] = useState('');
  const [trPair, setTrPair] = useState('en|ru'); // 'en|ru' | 'ru|en' | 'es|ru' | 'ru|es'
  const [trResult, setTrResult] = useState('');
  const [trLoading, setTrLoading] = useState(false);
  const [trError, setTrError] = useState('');
  const [trCopied, setTrCopied] = useState(false);
  const [dict, setDict] = useState([]); // словарь: [{id, src, dst}]
  const [dictSrc, setDictSrc] = useState('');
  const [dictDst, setDictDst] = useState('');
  const PAIRS = [{
    id: 'en|ru',
    label: '🇬🇧 Английский → 🇷🇺 Русский'
  }, {
    id: 'ru|en',
    label: '🇷🇺 Русский → 🇬🇧 Английский'
  }, {
    id: 'es|ru',
    label: '🇪🇸 Испанский → 🇷🇺 Русский'
  }, {
    id: 'ru|es',
    label: '🇷🇺 Русский → 🇪🇸 Испанский'
  }];

  // словарь в localStorage
  useEffect(() => {
    try {
      const raw = localStorage.getItem('hub_dict');
      if (raw) setDict(JSON.parse(raw));
    } catch (_) {}
  }, []);
  const saveDict = d => {
    setDict(d);
    try {
      localStorage.setItem('hub_dict', JSON.stringify(d));
    } catch (_) {}
  };
  const addDict = (src, dst) => {
    if (!src.trim()) return;
    saveDict([{
      id: Date.now(),
      src: src.trim(),
      dst: (dst || '').trim()
    }, ...dict]);
  };
  const removeDict = id => saveDict(dict.filter(x => x.id !== id));
  const doTranslate = () => {
    if (!trText.trim()) {
      setTrError('Введи текст для перевода');
      return;
    }
    setTrLoading(true);
    setTrError('');
    setTrResult('');
    const [from, to] = trPair.split('|');
    apiFetch('/miniapp/api/translate', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        text: trText,
        from,
        to
      })
    }).then(r => r.json()).then(d => {
      if (d.ok) setTrResult(d.text || '');else setTrError(d.error || 'Ошибка перевода');
    }).catch(() => setTrError('Сервер недоступен')).finally(() => setTrLoading(false));
  };
  const priceLabel = p => {
    if (p === undefined || p === null) return '';
    if (p === 0) return 'Бесплатно';
    if (p < 0.3) return 'Дёшево';
    if (p < 0.7) return 'Средне';
    return 'Дорого';
  };
  const accessLabel = a => {
    if (a === undefined || a === null) return '';
    if (a < 0.3) return 'Легко организовать';
    if (a < 0.7) return 'Средняя сложность';
    return 'Сложно организовать';
  };
  return /*#__PURE__*/React.createElement("div", {
    className: "max-w-xl mx-auto font-sans pb-4"
  }, auth.state === 'loading' && /*#__PURE__*/React.createElement("div", {
    className: "flex flex-col items-center justify-center py-32 space-y-3"
  }, /*#__PURE__*/React.createElement("div", {
    className: "w-10 h-10 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"
  }), /*#__PURE__*/React.createElement("div", {
    className: "text-xs font-bold text-slate-500"
  }, "\u041F\u0440\u043E\u0432\u0435\u0440\u044F\u0435\u043C \u0430\u0432\u0442\u043E\u0440\u0438\u0437\u0430\u0446\u0438\u044E\u2026")), auth.state === 'login' && /*#__PURE__*/React.createElement("div", {
    className: "flex flex-col items-center justify-center min-h-[80vh] px-6 text-center"
  }, /*#__PURE__*/React.createElement("div", {
    className: "card p-8 w-full max-w-xs space-y-4"
  }, /*#__PURE__*/React.createElement("div", {
    className: "w-16 h-16 rounded-2xl bg-accent-soft flex items-center justify-center mx-auto"
  }, /*#__PURE__*/React.createElement("i", {
    className: "ph ph-fingerprint-simple",
    style: {
      fontSize: '32px',
      color: 'var(--accent)'
    }
  })), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    className: "text-xl font-bold",
    style: {
      color: 'var(--text)'
    }
  }, "R2D2"), /*#__PURE__*/React.createElement("div", {
    className: "text-[11px] font-medium",
    style: {
      color: 'var(--text-muted)'
    }
  }, "\u043C\u0438\u043D\u0438-\u043F\u0440\u0438\u043B\u043E\u0436\u0435\u043D\u0438\u0435")), /*#__PURE__*/React.createElement("div", {
    className: "text-xs leading-relaxed",
    style: {
      color: 'var(--text-muted)'
    }
  }, "\u0412\u0445\u043E\u0434 \u0447\u0435\u0440\u0435\u0437 Telegram. \u0414\u043B\u044F \u043F\u043E\u0434\u0442\u0432\u0435\u0440\u0436\u0434\u0435\u043D\u0438\u044F \u043C\u043E\u0436\u0435\u0442 \u043F\u043E\u0442\u0440\u0435\u0431\u043E\u0432\u0430\u0442\u044C\u0441\u044F FaceID / Touch ID."), authError && /*#__PURE__*/React.createElement("div", {
    className: "text-xs font-bold text-red-500 bg-red-50 border border-red-200 rounded-xl px-3 py-2"
  }, authError), /*#__PURE__*/React.createElement("button", {
    onClick: doLogin,
    className: "w-full py-3.5 rounded-2xl font-bold text-sm text-white transition active:scale-95",
    style: {
      background: 'var(--accent)',
      boxShadow: '0 8px 20px rgba(89,100,232,0.3)'
    }
  }, "\u0412\u043E\u0439\u0442\u0438 \u0441 FaceID"), bioStatus && /*#__PURE__*/React.createElement("div", {
    className: "text-[10px] font-semibold px-3 py-2 rounded-xl border leading-relaxed",
    style: {
      color: 'var(--text-muted)',
      background: 'var(--surface-subtle)',
      borderColor: 'var(--border)'
    }
  }, bioStatus), /*#__PURE__*/React.createElement("button", {
    onClick: () => {
      haptic('light');
      setPassState(s => ({
        ...s,
        showLogin: !s.showLogin,
        msg: ''
      }));
    },
    className: "text-xs font-bold underline underline-offset-2 active:scale-95 transition",
    style: {
      color: 'var(--accent)'
    }
  }, passState.showLogin ? 'Скрыть' : 'Войти с паролем (десктоп)'), passState.showLogin && /*#__PURE__*/React.createElement("div", {
    className: "space-y-2"
  }, /*#__PURE__*/React.createElement("input", {
    type: "text",
    placeholder: "\u041B\u043E\u0433\u0438\u043D (username Telegram)",
    value: passState.login,
    onChange: e => setPassState(s => ({
      ...s,
      login: e.target.value
    })),
    className: "w-full text-xs rounded-xl px-3 py-2.5 focus:outline-none border",
    style: {
      background: 'var(--surface-subtle)',
      borderColor: 'var(--border)',
      color: 'var(--text)'
    }
  }), /*#__PURE__*/React.createElement("input", {
    type: "password",
    placeholder: "\u041F\u0430\u0440\u043E\u043B\u044C",
    value: passState.pwd,
    onChange: e => setPassState(s => ({
      ...s,
      pwd: e.target.value
    })),
    onKeyDown: e => {
      if (e.key === 'Enter') doLoginPassword();
    },
    className: "w-full text-xs rounded-xl px-3 py-2.5 focus:outline-none border",
    style: {
      background: 'var(--surface-subtle)',
      borderColor: 'var(--border)',
      color: 'var(--text)'
    }
  }), passState.msg && /*#__PURE__*/React.createElement("div", {
    className: "text-[10px] font-bold text-red-500"
  }, passState.msg), /*#__PURE__*/React.createElement("button", {
    onClick: doLoginPassword,
    className: "w-full py-2.5 text-white rounded-xl font-bold text-xs transition active:scale-95",
    style: {
      background: 'var(--accent)'
    }
  }, "\u0412\u043E\u0439\u0442\u0438"), /*#__PURE__*/React.createElement("div", {
    className: "pt-2 border-t space-y-2",
    style: {
      borderColor: 'var(--border)'
    }
  }, /*#__PURE__*/React.createElement("div", {
    className: "text-[10px] font-bold uppercase tracking-wide",
    style: {
      color: 'var(--text-muted)'
    }
  }, "\u0412\u043F\u0435\u0440\u0432\u044B\u0435? \u0417\u0430\u0434\u0430\u0439\u0442\u0435 \u043F\u0430\u0440\u043E\u043B\u044C"), /*#__PURE__*/React.createElement("input", {
    type: "password",
    placeholder: "\u041D\u043E\u0432\u044B\u0439 \u043F\u0430\u0440\u043E\u043B\u044C (\u043C\u0438\u043D. 4 \u0441\u0438\u043C\u0432\u043E\u043B\u0430)",
    value: passState.setPwd,
    onChange: e => setPassState(s => ({
      ...s,
      setPwd: e.target.value
    })),
    className: "w-full text-xs rounded-xl px-3 py-2.5 focus:outline-none border",
    style: {
      background: 'var(--surface-subtle)',
      borderColor: 'var(--border)',
      color: 'var(--text)'
    }
  }), /*#__PURE__*/React.createElement("button", {
    onClick: setPasswordOnLogin,
    className: "w-full py-2.5 text-white rounded-xl font-bold text-xs transition active:scale-95",
    style: {
      background: 'var(--text)'
    }
  }, "\u0417\u0430\u0434\u0430\u0442\u044C \u043F\u0430\u0440\u043E\u043B\u044C"))))), auth.state === 'ok' && view === 'main' && /*#__PURE__*/React.createElement("div", {
    className: "space-y-5 pb-4"
  }, /*#__PURE__*/React.createElement("div", {
    className: "header"
  }, /*#__PURE__*/React.createElement("div", {
    className: "btn",
    onClick: () => {
      try {
        window.Telegram?.WebApp?.close();
      } catch (e) {}
    }
  }, /*#__PURE__*/React.createElement("i", {
    className: "ph ph-x"
  })), /*#__PURE__*/React.createElement("div", {
    className: "mid"
  }, /*#__PURE__*/React.createElement("div", {
    className: "title"
  }, new Date().toLocaleDateString('ru-RU', {
    weekday: 'long',
    day: 'numeric',
    month: 'long'
  })), /*#__PURE__*/React.createElement("div", {
    className: "subtitle"
  }, new Date().toLocaleTimeString('ru-RU', {
    hour: '2-digit',
    minute: '2-digit'
  }))), /*#__PURE__*/React.createElement("div", {
    className: "btn",
    onClick: () => {
      haptic();
      setPassState(s => ({
        ...s,
        showSet: !s.showSet,
        msg: ''
      }));
    }
  }, /*#__PURE__*/React.createElement("i", {
    className: "ph ph-dots-three"
  }))), auth.user && /*#__PURE__*/React.createElement("div", {
    className: "flex items-center justify-between px-4 -mt-1"
  }, /*#__PURE__*/React.createElement("div", {
    className: "flex items-center gap-2"
  }, /*#__PURE__*/React.createElement("div", {
    className: "w-8 h-8 rounded-full flex items-center justify-center",
    style: {
      background: 'var(--accent-soft)',
      color: 'var(--accent)'
    }
  }, /*#__PURE__*/React.createElement("i", {
    className: "ph ph-user-circle",
    style: {
      fontSize: '20px'
    }
  })), /*#__PURE__*/React.createElement("span", {
    className: "text-sm font-bold",
    style: {
      color: 'var(--text)'
    }
  }, auth.user.first_name || auth.user.username || 'Пользователь'), auth.user.role === 'admin' && /*#__PURE__*/React.createElement("span", {
    className: "text-[10px] font-bold px-1.5 py-0.5 rounded-lg",
    style: {
      color: 'var(--accent)',
      background: 'var(--accent-soft)',
      border: '1px solid var(--accent-soft)'
    }
  }, "admin")), /*#__PURE__*/React.createElement("div", {
    className: "flex items-center gap-1.5"
  }, auth.user.role === 'admin' && /*#__PURE__*/React.createElement("button", {
    onClick: () => {
      haptic();
      setView('admin');
    },
    className: "text-xs font-bold px-3 py-1.5 rounded-lg active:scale-95 transition",
    style: {
      color: 'var(--accent)',
      background: 'var(--accent-soft)'
    }
  }, "\u0410\u0434\u043C\u0438\u043D"), /*#__PURE__*/React.createElement("button", {
    onClick: doLogout,
    className: "text-xs font-bold px-3 py-1.5 rounded-lg active:scale-95 transition",
    style: {
      color: 'var(--text-muted)',
      background: 'var(--surface-subtle)',
      border: '1px solid var(--border)'
    }
  }, "\u0412\u044B\u0439\u0442\u0438"))), passState.showSet && /*#__PURE__*/React.createElement("div", {
    className: "card p-4 space-y-2"
  }, /*#__PURE__*/React.createElement("div", {
    className: "b-title"
  }, "\uD83D\uDD11 \u041F\u0430\u0440\u043E\u043B\u044C \u0434\u043B\u044F \u0432\u0445\u043E\u0434\u0430 \u043D\u0430 \u0434\u0435\u0441\u043A\u0442\u043E\u043F\u0435"), /*#__PURE__*/React.createElement("div", {
    className: "text-[10px] text-slate-500"
  }, "\u0417\u0430\u0434\u0430\u0439 \u0441\u0432\u043E\u0439 \u043F\u0430\u0440\u043E\u043B\u044C \u2014 \u0438\u043C \u0431\u0443\u0434\u0435\u0448\u044C \u0432\u0445\u043E\u0434\u0438\u0442\u044C \u043D\u0430 Mac/\u0431\u0440\u0430\u0443\u0437\u0435\u0440\u0435 (\u043B\u043E\u0433\u0438\u043D: \u0442\u0432\u043E\u0439 username Telegram)"), /*#__PURE__*/React.createElement("input", {
    type: "password",
    placeholder: "\u041D\u043E\u0432\u044B\u0439 \u043F\u0430\u0440\u043E\u043B\u044C (\u043C\u0438\u043D. 4 \u0441\u0438\u043C\u0432\u043E\u043B\u0430)",
    value: passState.newPass,
    onChange: e => setPassState(s => ({
      ...s,
      newPass: e.target.value
    })),
    className: "w-full bg-slate-50 border-2 border-slate-200 text-xs rounded-xl px-3 py-2.5 focus:outline-none focus:border-blue-600"
  }), passState.msg && /*#__PURE__*/React.createElement("div", {
    className: "text-[10px] font-bold text-blue-600"
  }, passState.msg), /*#__PURE__*/React.createElement("button", {
    onClick: setMyPassword,
    className: "w-full py-2.5 bg-slate-900 text-white rounded-xl font-bold text-xs transition active:scale-95"
  }, "\u0421\u043E\u0445\u0440\u0430\u043D\u0438\u0442\u044C \u043F\u0430\u0440\u043E\u043B\u044C")), /*#__PURE__*/React.createElement("div", {
    className: "summary"
  }, /*#__PURE__*/React.createElement("div", {
    className: "pill",
    onClick: () => {
      haptic();
      document.getElementById('tasksBlock')?.scrollIntoView({
        behavior: 'smooth',
        block: 'start'
      });
    }
  }, /*#__PURE__*/React.createElement("div", {
    className: "ic"
  }, /*#__PURE__*/React.createElement("i", {
    className: "ph ph-checks"
  })), /*#__PURE__*/React.createElement("div", {
    className: "txt"
  }, activeTasks.length, " \u0437\u0430\u0434\u0430\u0447"), /*#__PURE__*/React.createElement("div", {
    className: "chev"
  }, "\u203A")), /*#__PURE__*/React.createElement("div", {
    className: "pill",
    onClick: () => {
      haptic('medium');
      setView('digest');
    }
  }, /*#__PURE__*/React.createElement("div", {
    className: "ic"
  }, /*#__PURE__*/React.createElement("i", {
    className: "ph ph-newspaper"
  })), /*#__PURE__*/React.createElement("div", {
    className: "txt"
  }, "\u0414\u0430\u0439\u0434\u0436\u0435\u0441\u0442"), /*#__PURE__*/React.createElement("div", {
    className: "chev"
  }, "\u203A")), /*#__PURE__*/React.createElement("div", {
    className: "pill",
    onClick: () => {
      haptic('medium');
      setShowRates(true);
      setView('main');
      setTimeout(() => document.getElementById('ratesBlock')?.scrollIntoView({
        behavior: 'smooth',
        block: 'start'
      }), 120);
    }
  }, /*#__PURE__*/React.createElement("div", {
    className: "ic"
  }, /*#__PURE__*/React.createElement("i", {
    className: "ph ph-coins"
  })), /*#__PURE__*/React.createElement("div", {
    className: "txt"
  }, rates.USD ? Math.round(rates.USD) : '—', " \u20BD/$"), /*#__PURE__*/React.createElement("div", {
    className: "chev"
  }, "\u203A"))), /*#__PURE__*/React.createElement("section", {
    className: "weather-card",
    style: {
      backgroundImage: `url('weather-assets/card-backgrounds/${(() => {
        const n = isNightTime();
        const map = {
          'clear-day': n ? 'clear-night' : 'sunny-background',
          'partly-cloudy-day': n ? 'partly-cloudy-night' : 'partly-cloudy-background',
          'cloudy': n ? 'cloudy-night' : 'cloudy-background',
          'overcast': n ? 'cloudy-night' : 'overcast-background',
          'fog': n ? 'cloudy-night' : 'fog-background',
          'drizzle': n ? 'rain-night' : 'drizzle-background',
          'rain': n ? 'rain-night' : 'rain-background',
          'thunderstorms': n ? 'thunderstorm-night' : 'thunderstorm-background',
          'snow': n ? 'snow-night' : 'snow-background',
          'sleet': n ? 'snow-night' : 'sleet-background',
          'wind': n ? 'cloudy-night' : 'wind-background',
          'clear-night': 'clear-night',
          'partly-cloudy-night': 'partly-cloudy-night'
        };
        return (map[weather.icon] || 'partly-cloudy-background') + '.png?v=7';
      })()}'`,
      backgroundSize: 'cover',
      backgroundPosition: 'right center'
    },
    "aria-label": "\u041F\u043E\u0433\u043E\u0434\u0430 \u0432 \u041C\u043E\u0441\u043A\u0432\u0435"
  }, /*#__PURE__*/React.createElement("div", {
    className: "weather-card__top"
  }, /*#__PURE__*/React.createElement("div", {
    className: "weather-card__content"
  }, /*#__PURE__*/React.createElement("div", {
    className: "weather-card__city"
  }, weather.city), /*#__PURE__*/React.createElement("div", {
    className: "weather-card__temp"
  }, weather.temp, /*#__PURE__*/React.createElement("sup", null, "\xB0C")), /*#__PURE__*/React.createElement("div", {
    className: "weather-card__desc"
  }, weather.condition), /*#__PURE__*/React.createElement("div", {
    className: "weather-card__wind"
  }, "\u0412\u0435\u0442\u0435\u0440 ", weather.wind))), /*#__PURE__*/React.createElement("div", {
    className: "weather-card__divider"
  }), /*#__PURE__*/React.createElement("div", {
    className: "weather-card__hourly"
  }, om && om.hourly ? (() => {
    const nowTs = Date.now();
    let startIdx = om.hourly.time.findIndex(t => new Date(t).getTime() >= nowTs - 60 * 60 * 1000);
    if (startIdx < 0) startIdx = 0;
    return om.hourly.time.slice(startIdx, startIdx + 10).map((t, i) => {
      const j = startIdx + i;
      const r = om.hourly.rain?.[j] || 0;
      const s = om.hourly.snowfall?.[j] || 0;
      const wc = om.hourly.weathercode?.[j] ?? 0;
      const total = r + s;
      let icon;
      if (total > 0) {
        icon = total < 0.3 ? 'drizzle' : total < 3 ? 'rain' : 'thunderstorms';
      } else {
        icon = wc === 0 ? 'clear-day' : wc <= 2 ? 'partly-cloudy-day' : wc >= 95 ? 'thunderstorms' : wc >= 80 ? 'rain' : wc >= 71 ? 'snow' : wc >= 61 ? 'rain' : wc >= 51 ? 'drizzle' : wc >= 45 ? 'fog' : 'cloudy';
      }
      return /*#__PURE__*/React.createElement("div", {
        key: t,
        className: "h-item"
      }, /*#__PURE__*/React.createElement("div", {
        className: "h-time"
      }, new Date(t).toLocaleTimeString('ru-RU', {
        hour: '2-digit',
        minute: '2-digit'
      })), /*#__PURE__*/React.createElement("img", {
        className: "h-ic",
        src: 'weather-icons/meteocons/' + icon + '.svg',
        alt: ""
      }), /*#__PURE__*/React.createElement("div", {
        className: "h-t"
      }, Math.round(om.hourly.temperature_2m[j]), "\xB0"));
    });
  })() : /*#__PURE__*/React.createElement("div", {
    className: "h-item"
  }, /*#__PURE__*/React.createElement("div", {
    className: "h-time"
  }, "--:--"), /*#__PURE__*/React.createElement("div", {
    className: "h-t"
  }, "\u2014\xB0")))), /*#__PURE__*/React.createElement("div", {
    className: "card",
    id: "ratesBlock"
  }, /*#__PURE__*/React.createElement("div", {
    className: "row",
    onClick: () => {
      haptic();
      setShowRates(!showRates);
    }
  }, /*#__PURE__*/React.createElement("div", {
    className: "ic"
  }, /*#__PURE__*/React.createElement("i", {
    className: "ph ph-coins"
  })), /*#__PURE__*/React.createElement("div", {
    className: "body"
  }, /*#__PURE__*/React.createElement("div", {
    className: "title"
  }, "\u0412\u0430\u043B\u044E\u0442\u044B & \u041A\u043E\u043D\u0432\u0435\u0440\u0442\u0435\u0440"), /*#__PURE__*/React.createElement("div", {
    className: "status"
  }, "\u041A\u0443\u0440\u0441\u044B \u0426\u0411 \u0420\u0424 \xB7 USD ", rates.USD ? Math.round(rates.USD) : '—', "\u20BD")), /*#__PURE__*/React.createElement("div", {
    className: "chev"
  }, showRates ? '▲' : '▼')), showRates && /*#__PURE__*/React.createElement("div", {
    className: "block space-y-2.5"
  }, /*#__PURE__*/React.createElement("div", {
    className: "flex items-center gap-2"
  }, /*#__PURE__*/React.createElement("input", {
    type: "number",
    value: calcAmount,
    onChange: e => setCalcAmount(Number(e.target.value)),
    className: "flex-1 min-w-0 basis-20 rounded-xl px-3 py-2.5 text-base font-bold outline-none border",
    style: {
      background: 'var(--surface-subtle)',
      borderColor: 'var(--border)',
      color: 'var(--text)'
    }
  }), /*#__PURE__*/React.createElement("select", {
    value: fromCurr,
    onChange: e => setFromCurr(e.target.value),
    className: "shrink-0 rounded-xl px-2 py-2.5 text-xs font-bold outline-none border",
    style: {
      background: 'var(--surface-subtle)',
      borderColor: 'var(--border)',
      color: 'var(--text)'
    }
  }, ['USD', 'EUR', 'CNY', 'JPY', 'GBP', 'RUB'].map(c => /*#__PURE__*/React.createElement("option", {
    key: c,
    value: c
  }, c))), /*#__PURE__*/React.createElement("i", {
    className: "ph ph-arrow-right shrink-0",
    style: {
      color: 'var(--text-muted)',
      fontSize: '16px'
    }
  }), /*#__PURE__*/React.createElement("select", {
    value: toCurr,
    onChange: e => setToCurr(e.target.value),
    className: "shrink-0 rounded-xl px-2 py-2.5 text-xs font-bold outline-none border",
    style: {
      background: 'var(--surface-subtle)',
      borderColor: 'var(--border)',
      color: 'var(--text)'
    }
  }, ['RUB', 'USD', 'EUR', 'CNY', 'JPY', 'GBP'].map(c => /*#__PURE__*/React.createElement("option", {
    key: c,
    value: c
  }, c)))), /*#__PURE__*/React.createElement("div", {
    className: "flex items-center justify-between rounded-xl px-3.5 py-3",
    style: {
      background: 'rgba(16,185,129,0.08)',
      border: '1px solid rgba(16,185,129,0.25)'
    }
  }, /*#__PURE__*/React.createElement("span", {
    className: "text-[10px] font-bold uppercase tracking-wide",
    style: {
      color: 'var(--text-muted)'
    }
  }, "\u0420\u0435\u0437\u0443\u043B\u044C\u0442\u0430\u0442"), /*#__PURE__*/React.createElement("span", {
    className: "text-base font-black",
    style: {
      color: '#059669',
      fontVariantNumeric: 'tabular-nums',
      lineHeight: 1.2
    }
  }, convertValue(), " ", toCurr)))), /*#__PURE__*/React.createElement("div", {
    className: "card",
    id: "tasksBlock"
  }, /*#__PURE__*/React.createElement("div", {
    className: "row",
    onClick: () => {
      haptic();
      setView('archive');
    }
  }, /*#__PURE__*/React.createElement("div", {
    className: "ic acc"
  }, /*#__PURE__*/React.createElement("i", {
    className: "ph ph-checks"
  })), /*#__PURE__*/React.createElement("div", {
    className: "body"
  }, /*#__PURE__*/React.createElement("div", {
    className: "title"
  }, "\u0417\u0430\u0434\u0430\u0447\u0438"), /*#__PURE__*/React.createElement("div", {
    className: "status"
  }, activeTasks.length, " \u0430\u043A\u0442\u0438\u0432\u043D\u044B\u0445 \xB7 ", completedTasks.length, " \u0432 \u0430\u0440\u0445\u0438\u0432\u0435")), /*#__PURE__*/React.createElement("div", {
    className: "chev"
  }, "\u203A")), /*#__PURE__*/React.createElement("div", {
    className: "block space-y-2"
  }, activeTasks.map(t => /*#__PURE__*/React.createElement("div", {
    key: t.id,
    className: "flex items-center gap-3 p-3 bg-slate-50 border border-slate-200 rounded-2xl"
  }, /*#__PURE__*/React.createElement("div", {
    onClick: () => toggleTask(t.id),
    className: "w-6 h-6 rounded-lg border-2 border-slate-300 flex items-center justify-center bg-white shrink-0 active:scale-90 transition cursor-pointer"
  }, t.done && /*#__PURE__*/React.createElement("span", {
    className: "text-blue-600 text-xs font-black"
  }, "\u2713")), /*#__PURE__*/React.createElement("div", {
    className: "flex-1 min-w-0"
  }, /*#__PURE__*/React.createElement("div", {
    className: "text-[10px] font-mono text-slate-400"
  }, "\uD83D\uDD52 ", t.createdAt), /*#__PURE__*/React.createElement("div", {
    className: "text-xs font-bold text-slate-800 leading-snug"
  }, t.text)), /*#__PURE__*/React.createElement("button", {
    onClick: e => {
      e.stopPropagation();
      deleteTask(t.id);
    },
    className: "text-slate-300 hover:text-red-500 text-sm font-black shrink-0 px-1"
  }, "\xD7"))), activeTasks.length === 0 && /*#__PURE__*/React.createElement("div", {
    className: "text-center py-3 text-xs text-slate-400"
  }, "\u0412\u0441\u0435 \u0434\u0435\u043B\u0430 \u0432\u044B\u043F\u043E\u043B\u043D\u0435\u043D\u044B! \u0414\u043E\u0431\u0430\u0432\u044C \u043D\u043E\u0432\u0443\u044E \u0437\u0430\u0434\u0430\u0447\u0443 \u043D\u0438\u0436\u0435."), /*#__PURE__*/React.createElement("div", {
    className: "flex gap-2 pt-1"
  }, /*#__PURE__*/React.createElement("input", {
    type: "text",
    placeholder: "\u041D\u043E\u0432\u0430\u044F \u0437\u0430\u0434\u0430\u0447\u0430...",
    value: taskInput,
    onChange: e => setTaskInput(e.target.value),
    onKeyDown: e => {
      if (e.key === 'Enter') handleAddTask();
    },
    className: "flex-1 bg-slate-50 border-2 border-slate-200 text-xs rounded-2xl px-4 py-3 focus:outline-none focus:border-blue-600"
  }), /*#__PURE__*/React.createElement("button", {
    type: "button",
    onClick: startVoiceInput,
    title: "\u041D\u0430\u0434\u0438\u043A\u0442\u043E\u0432\u0430\u0442\u044C \u0433\u043E\u043B\u043E\u0441\u043E\u043C",
    className: "px-4 py-3 bg-blue-50 active:scale-95 text-blue-600 rounded-2xl font-black text-lg transition border border-blue-200"
  }, "\uD83C\uDFA4"), /*#__PURE__*/React.createElement("button", {
    type: "button",
    onClick: () => handleAddTask(),
    className: "px-5 py-3 bg-slate-900 active:scale-95 text-white rounded-2xl font-black text-lg transition"
  }, "+")), voiceError && /*#__PURE__*/React.createElement("div", {
    className: "text-[10px] font-bold text-red-500"
  }, voiceError))), /*#__PURE__*/React.createElement("div", {
    className: "card"
  }, /*#__PURE__*/React.createElement("div", {
    className: "row",
    onClick: () => {
      haptic();
      document.getElementById('calBlock')?.scrollIntoView({
        behavior: 'smooth'
      });
    }
  }, /*#__PURE__*/React.createElement("div", {
    className: "ic"
  }, /*#__PURE__*/React.createElement("i", {
    className: "ph ph-calendar-dots"
  })), /*#__PURE__*/React.createElement("div", {
    className: "body"
  }, /*#__PURE__*/React.createElement("div", {
    className: "title"
  }, "\u041A\u0430\u043B\u0435\u043D\u0434\u0430\u0440\u044C"), /*#__PURE__*/React.createElement("div", {
    className: "status"
  }, "Google Calendar \xB7 7 \u0434\u043D\u0435\u0439")), /*#__PURE__*/React.createElement("div", {
    className: "chev"
  }, "\u203A")), /*#__PURE__*/React.createElement("div", {
    className: "block",
    id: "calBlock"
  }, calendarError ? /*#__PURE__*/React.createElement("div", {
    className: "text-xs text-red-500"
  }, calendarError) : !calendarData ? /*#__PURE__*/React.createElement("div", {
    className: "text-center py-2 text-xs text-slate-400"
  }, "\u0417\u0430\u0433\u0440\u0443\u0436\u0430\u0435\u043C \u0441\u043E\u0431\u044B\u0442\u0438\u044F\u2026") : /*#__PURE__*/React.createElement("div", {
    className: "space-y-2"
  }, calendarData.days && calendarData.days.filter(d => d.events.length > 0).length === 0 && /*#__PURE__*/React.createElement("div", {
    className: "text-center py-2 text-xs text-slate-400"
  }, "\u041D\u0430 \u0431\u043B\u0438\u0436\u0430\u0439\u0448\u0438\u0435 7 \u0434\u043D\u0435\u0439 \u0441\u043E\u0431\u044B\u0442\u0438\u0439 \u043D\u0435\u0442."), calendarData.days && calendarData.days.map(d => d.events.length > 0 && /*#__PURE__*/React.createElement("div", {
    key: d.date,
    className: "bg-slate-50 border border-slate-200 rounded-2xl p-3"
  }, /*#__PURE__*/React.createElement("div", {
    className: "text-[10px] font-bold text-slate-500 uppercase tracking-wide mb-1.5"
  }, d.label), /*#__PURE__*/React.createElement("div", {
    className: "space-y-1.5"
  }, d.events.map((ev, i) => /*#__PURE__*/React.createElement("div", {
    key: i,
    className: "flex items-start gap-2"
  }, /*#__PURE__*/React.createElement("span", {
    className: "font-mono text-xs font-black text-blue-600 shrink-0 mt-0.5"
  }, ev.time), /*#__PURE__*/React.createElement("div", {
    className: "min-w-0 flex-1"
  }, /*#__PURE__*/React.createElement("div", {
    className: "text-xs font-bold text-slate-800 leading-snug"
  }, ev.summary), ev.location && /*#__PURE__*/React.createElement("div", {
    className: "text-[10px] text-slate-400 truncate"
  }, "\uD83D\uDCCD ", ev.location)))))))))), /*#__PURE__*/React.createElement("div", {
    className: "card"
  }, /*#__PURE__*/React.createElement("div", {
    className: "row",
    onClick: () => {
      haptic();
      setShowPass(!showPass);
    }
  }, /*#__PURE__*/React.createElement("div", {
    className: "ic"
  }, /*#__PURE__*/React.createElement("i", {
    className: "ph ph-key"
  })), /*#__PURE__*/React.createElement("div", {
    className: "body"
  }, /*#__PURE__*/React.createElement("div", {
    className: "title"
  }, "\u041F\u0430\u0440\u043E\u043B\u0438"), /*#__PURE__*/React.createElement("div", {
    className: "status"
  }, "\u0413\u0435\u043D\u0435\u0440\u0430\u0442\u043E\u0440 \u043D\u0430\u0434\u0451\u0436\u043D\u044B\u0445 \u043F\u0430\u0440\u043E\u043B\u0435\u0439")), /*#__PURE__*/React.createElement("div", {
    className: "chev"
  }, showPass ? '▲' : '▼')), showPass && /*#__PURE__*/React.createElement("div", {
    className: "block space-y-3"
  }, /*#__PURE__*/React.createElement("input", {
    type: "range",
    min: "12",
    max: "32",
    value: passLength,
    onChange: e => setPassLength(Number(e.target.value)),
    className: "w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
  }), /*#__PURE__*/React.createElement("div", {
    className: "text-xs font-black text-blue-600 font-mono"
  }, passLength, " \u0441\u0438\u043C\u0432."), /*#__PURE__*/React.createElement("div", {
    onClick: copyToClipboard,
    className: "p-3.5 bg-slate-50 border-2 border-dashed border-slate-300 rounded-2xl flex items-center justify-between cursor-pointer active:scale-98 transition"
  }, /*#__PURE__*/React.createElement("span", {
    className: "font-mono text-xs font-bold break-all"
  }, password), /*#__PURE__*/React.createElement("span", {
    className: "text-xs font-bold text-blue-600 ml-2 shrink-0"
  }, copied ? 'Скопировано ✓' : 'Копировать')), /*#__PURE__*/React.createElement("button", {
    onClick: generatePassword,
    className: "w-full py-3 bg-slate-900 active:scale-98 text-white rounded-2xl font-bold text-xs transition"
  }, "\u0421\u0433\u0435\u043D\u0435\u0440\u0438\u0440\u043E\u0432\u0430\u0442\u044C \u043D\u043E\u0432\u044B\u0439 \u043F\u0430\u0440\u043E\u043B\u044C"))), /*#__PURE__*/React.createElement("div", {
    className: "card"
  }, /*#__PURE__*/React.createElement("div", {
    className: "row",
    onClick: () => {
      haptic('medium');
      setView('fun');
    }
  }, /*#__PURE__*/React.createElement("div", {
    className: "ic"
  }, /*#__PURE__*/React.createElement("i", {
    className: "ph ph-brain"
  })), /*#__PURE__*/React.createElement("div", {
    className: "body"
  }, /*#__PURE__*/React.createElement("div", {
    className: "title"
  }, "\u0412\u0438\u043A\u0442\u043E\u0440\u0438\u043D\u044B & \u0418\u0434\u0435\u0438"), /*#__PURE__*/React.createElement("div", {
    className: "status"
  }, "\u0412\u043E\u043F\u0440\u043E\u0441\u044B + \u0447\u0435\u043C \u0437\u0430\u043D\u044F\u0442\u044C\u0441\u044F")), /*#__PURE__*/React.createElement("div", {
    className: "chev"
  }, "\u203A"))), /*#__PURE__*/React.createElement("div", {
    className: "card"
  }, /*#__PURE__*/React.createElement("div", {
    className: "row",
    onClick: () => {
      haptic('medium');
      setView('translate');
    }
  }, /*#__PURE__*/React.createElement("div", {
    className: "ic"
  }, /*#__PURE__*/React.createElement("i", {
    className: "ph ph-translate"
  })), /*#__PURE__*/React.createElement("div", {
    className: "body"
  }, /*#__PURE__*/React.createElement("div", {
    className: "title"
  }, "\u041F\u0435\u0440\u0435\u0432\u043E\u0434\u0447\u0438\u043A & \u0421\u043B\u043E\u0432\u0430\u0440\u044C"), /*#__PURE__*/React.createElement("div", {
    className: "status"
  }, "\u0410\u043D\u0433\u043B\u0438\u0439\u0441\u043A\u0438\u0439 \u2194 \u0440\u0443\u0441\u0441\u043A\u0438\u0439 \xB7 \u0438\u0441\u043F\u0430\u043D\u0441\u043A\u0438\u0439 \u2194 \u0440\u0443\u0441\u0441\u043A\u0438\u0439")), /*#__PURE__*/React.createElement("div", {
    className: "chev"
  }, "\u203A"))), auth.user?.role === 'admin' && /*#__PURE__*/React.createElement("div", {
    className: "card"
  }, /*#__PURE__*/React.createElement("div", {
    className: "row",
    onClick: () => {
      haptic();
      setView('admin');
    }
  }, /*#__PURE__*/React.createElement("div", {
    className: "ic acc"
  }, /*#__PURE__*/React.createElement("i", {
    className: "ph ph-shield-check"
  })), /*#__PURE__*/React.createElement("div", {
    className: "body"
  }, /*#__PURE__*/React.createElement("div", {
    className: "title"
  }, "\u0410\u0434\u043C\u0438\u043D-\u043F\u0430\u043D\u0435\u043B\u044C"), /*#__PURE__*/React.createElement("div", {
    className: "status"
  }, "\u041F\u043E\u043B\u044C\u0437\u043E\u0432\u0430\u0442\u0435\u043B\u0438 \u0438 \u0430\u0443\u0434\u0438\u0442")), /*#__PURE__*/React.createElement("div", {
    className: "chev"
  }, "\u203A"))), /*#__PURE__*/React.createElement("div", {
    className: "tabbar"
  }, /*#__PURE__*/React.createElement("div", {
    className: "tab active",
    onClick: () => {
      haptic();
      setView('main');
    }
  }, /*#__PURE__*/React.createElement("i", {
    className: "ti ph ph-house"
  }), /*#__PURE__*/React.createElement("div", {
    className: "tl"
  }, "\u0413\u043B\u0430\u0432\u043D\u0430\u044F")), /*#__PURE__*/React.createElement("div", {
    className: "tab",
    onClick: () => {
      haptic('medium');
      setView('digest');
    }
  }, /*#__PURE__*/React.createElement("i", {
    className: "ti ph ph-newspaper"
  }), /*#__PURE__*/React.createElement("div", {
    className: "tl"
  }, "\u0414\u0430\u0439\u0434\u0436\u0435\u0441\u0442")), /*#__PURE__*/React.createElement("div", {
    className: "tab",
    onClick: () => {
      haptic('medium');
      setView('fun');
    }
  }, /*#__PURE__*/React.createElement("i", {
    className: "ti ph ph-brain"
  }), /*#__PURE__*/React.createElement("div", {
    className: "tl"
  }, "\u0412\u0438\u043A\u0442\u043E\u0440\u0438\u043D\u044B")), /*#__PURE__*/React.createElement("div", {
    className: "tab",
    onClick: () => {
      haptic('medium');
      setView('translate');
    }
  }, /*#__PURE__*/React.createElement("i", {
    className: "ti ph ph-translate"
  }), /*#__PURE__*/React.createElement("div", {
    className: "tl"
  }, "\u041F\u0435\u0440\u0435\u0432\u043E\u0434")), auth.user?.role === 'admin' && /*#__PURE__*/React.createElement("div", {
    className: "tab",
    onClick: () => {
      haptic();
      setView('admin');
    }
  }, /*#__PURE__*/React.createElement("i", {
    className: "ti ph ph-shield-check"
  }), /*#__PURE__*/React.createElement("div", {
    className: "tl"
  }, "\u0410\u0434\u043C\u0438\u043D")))), auth.state === 'ok' && view === 'archive' && /*#__PURE__*/React.createElement("div", {
    className: "space-y-4 animate-fade-in pb-24"
  }, /*#__PURE__*/React.createElement("div", {
    className: "header"
  }, /*#__PURE__*/React.createElement("div", {
    className: "btn",
    onClick: () => {
      haptic();
      setView('main');
    }
  }, /*#__PURE__*/React.createElement("i", {
    className: "ph ph-arrow-left"
  })), /*#__PURE__*/React.createElement("div", {
    className: "mid"
  }, /*#__PURE__*/React.createElement("div", {
    className: "title"
  }, "\u0410\u0440\u0445\u0438\u0432 \u0434\u0435\u043B"), /*#__PURE__*/React.createElement("div", {
    className: "subtitle"
  }, "\u0412\u044B\u043F\u043E\u043B\u043D\u0435\u043D\u043D\u044B\u0435 \u0437\u0430\u0434\u0430\u0447\u0438")), completedTasks.length > 0 ? /*#__PURE__*/React.createElement("div", {
    className: "btn",
    onClick: clearArchive
  }, /*#__PURE__*/React.createElement("i", {
    className: "ph ph-trash"
  })) : /*#__PURE__*/React.createElement("div", {
    className: "btn",
    style: {
      opacity: 0.3
    }
  }, /*#__PURE__*/React.createElement("i", {
    className: "ph ph-trash"
  }))), /*#__PURE__*/React.createElement("div", {
    className: "space-y-2.5"
  }, completedTasks.map(t => /*#__PURE__*/React.createElement("div", {
    key: t.id,
    className: "flex items-center justify-between p-3.5 bg-white border border-slate-200 rounded-2xl shadow-sm"
  }, /*#__PURE__*/React.createElement("div", {
    onClick: () => toggleTask(t.id),
    className: "flex items-center gap-3 flex-1 cursor-pointer"
  }, /*#__PURE__*/React.createElement("div", {
    className: "w-6 h-6 rounded-lg bg-emerald-500 text-white flex items-center justify-center text-xs font-bold shrink-0"
  }, "\u2713"), /*#__PURE__*/React.createElement("span", {
    className: "text-xs font-semibold text-slate-400 line-through"
  }, t.text)), /*#__PURE__*/React.createElement("button", {
    onClick: () => deleteTask(t.id),
    className: "text-slate-300 hover:text-red-500 text-sm px-2 py-1 font-bold active:scale-90"
  }, "\u2715"))), completedTasks.length === 0 && /*#__PURE__*/React.createElement("div", {
    className: "text-center py-10 text-xs text-slate-400 card p-6"
  }, "\u0412 \u0430\u0440\u0445\u0438\u0432\u0435 \u043D\u0435\u0442 \u0432\u044B\u043F\u043E\u043B\u043D\u0435\u043D\u043D\u044B\u0445 \u0437\u0430\u0434\u0430\u0447."))), auth.state === 'ok' && view === 'sources' && /*#__PURE__*/React.createElement("div", {
    className: "space-y-4 animate-fade-in pb-24"
  }, /*#__PURE__*/React.createElement("div", {
    className: "header"
  }, /*#__PURE__*/React.createElement("div", {
    className: "btn",
    onClick: () => {
      haptic();
      setView('main');
    }
  }, /*#__PURE__*/React.createElement("i", {
    className: "ph ph-arrow-left"
  })), /*#__PURE__*/React.createElement("div", {
    className: "mid"
  }, /*#__PURE__*/React.createElement("div", {
    className: "title"
  }, "\u0418\u0441\u0442\u043E\u0447\u043D\u0438\u043A\u0438"), /*#__PURE__*/React.createElement("div", {
    className: "subtitle"
  }, "\u041A\u0430\u043D\u0430\u043B\u044B \u0438 RSS \u0434\u043B\u044F \u0434\u0430\u0439\u0434\u0436\u0435\u0441\u0442\u0430")), /*#__PURE__*/React.createElement("div", {
    className: "btn",
    onClick: () => {
      haptic();
      setSourceType(sourceType === 'TG' ? 'RSS' : 'TG');
    }
  }, /*#__PURE__*/React.createElement("i", {
    className: "ph ph-plus"
  }))), /*#__PURE__*/React.createElement("div", {
    className: "card"
  }, sources.map((s, si) => /*#__PURE__*/React.createElement("div", {
    key: s.id,
    className: si > 0 ? "row" : "row",
    style: si > 0 ? {
      borderTop: '1px solid var(--border)'
    } : {}
  }, /*#__PURE__*/React.createElement("div", {
    className: "ic"
  }, /*#__PURE__*/React.createElement("i", {
    className: s.type === 'TG' ? 'ph ph-paper-plane-tilt' : 'ph ph-rss'
  })), /*#__PURE__*/React.createElement("div", {
    className: "body"
  }, /*#__PURE__*/React.createElement("div", {
    className: "title"
  }, s.title || s.name), /*#__PURE__*/React.createElement("div", {
    className: "status"
  }, s.type === 'TG' ? 'Telegram-канал' : 'RSS-лента')), /*#__PURE__*/React.createElement("button", {
    onClick: () => deleteSource(s.id),
    className: "w-9 h-9 rounded-xl flex items-center justify-center transition active:scale-90",
    style: {
      background: 'var(--surface-subtle)',
      color: 'var(--text-muted)'
    }
  }, /*#__PURE__*/React.createElement("i", {
    className: "ph ph-trash",
    style: {
      fontSize: '16px'
    }
  })))), sources.length === 0 && /*#__PURE__*/React.createElement("div", {
    className: "p-6 text-center text-xs",
    style: {
      color: 'var(--text-muted)'
    }
  }, "\u041D\u0435\u0442 \u043F\u043E\u0434\u043A\u043B\u044E\u0447\u0451\u043D\u043D\u044B\u0445 \u0438\u0441\u0442\u043E\u0447\u043D\u0438\u043A\u043E\u0432.")), /*#__PURE__*/React.createElement("div", {
    className: "card p-4 space-y-3"
  }, /*#__PURE__*/React.createElement("div", {
    className: "flex gap-1.5 p-1.5 rounded-xl",
    style: {
      background: 'var(--surface-subtle)'
    }
  }, [{
    id: 'TG',
    label: 'Telegram',
    icon: 'ph-paper-plane-tilt'
  }, {
    id: 'RSS',
    label: 'RSS-лента',
    icon: 'ph-rss'
  }].map(t => /*#__PURE__*/React.createElement("button", {
    key: t.id,
    type: "button",
    onClick: () => setSourceType(t.id),
    className: "flex-1 flex items-center justify-center gap-1.5 py-2 rounded-lg font-bold text-xs transition active:scale-95",
    style: sourceType === t.id ? {
      background: 'var(--accent)',
      color: '#fff'
    } : {
      color: 'var(--text-muted)',
      background: 'transparent'
    }
  }, /*#__PURE__*/React.createElement("i", {
    className: 'ph ' + t.icon,
    style: {
      fontSize: '15px'
    }
  }), t.label))), /*#__PURE__*/React.createElement("input", {
    type: "text",
    placeholder: sourceType === 'TG' ? '@channel_name или t.me/...' : 'https://site.com/rss',
    value: sourceName,
    onChange: e => setSourceName(e.target.value),
    className: "w-full rounded-xl px-3.5 py-2.5 text-sm outline-none border",
    style: {
      background: 'var(--surface-subtle)',
      borderColor: 'var(--border)',
      color: 'var(--text)'
    }
  }), sourceError && /*#__PURE__*/React.createElement("div", {
    className: "text-xs font-bold px-3 py-2 rounded-xl",
    style: {
      color: '#EF4444',
      background: 'rgba(239,68,68,0.1)',
      border: '1px solid rgba(239,68,68,0.25)'
    }
  }, sourceError), /*#__PURE__*/React.createElement("button", {
    type: "button",
    onClick: handleAddSource,
    className: "w-full py-3 rounded-xl font-bold text-sm transition active:scale-95 text-white",
    style: {
      background: 'var(--accent)'
    }
  }, "\u041F\u043E\u0434\u043A\u043B\u044E\u0447\u0438\u0442\u044C \u0438\u0441\u0442\u043E\u0447\u043D\u0438\u043A"))), auth.state === 'ok' && view === 'admin' && /*#__PURE__*/React.createElement(AdminPanel, {
    auth: auth,
    apiFetch: apiFetch,
    haptic: haptic,
    onBack: () => setView('main')
  }), auth.state === 'ok' && view === 'digest' && /*#__PURE__*/React.createElement("div", {
    className: "space-y-4 animate-fade-in pb-24"
  }, /*#__PURE__*/React.createElement("div", {
    className: "header"
  }, /*#__PURE__*/React.createElement("div", {
    className: "btn",
    onClick: () => {
      haptic();
      setView('main');
    }
  }, /*#__PURE__*/React.createElement("i", {
    className: "ph ph-arrow-left"
  })), /*#__PURE__*/React.createElement("div", {
    className: "mid"
  }, /*#__PURE__*/React.createElement("div", {
    className: "title"
  }, "\u0414\u0430\u0439\u0434\u0436\u0435\u0441\u0442"), /*#__PURE__*/React.createElement("div", {
    className: "subtitle"
  }, sources.length, " \u0438\u0441\u0442\u043E\u0447\u043D\u0438\u043A\u043E\u0432")), /*#__PURE__*/React.createElement("div", {
    className: "btn",
    onClick: () => {
      haptic('light');
      loadDigest();
    }
  }, /*#__PURE__*/React.createElement("i", {
    className: "ph ph-arrows-clockwise"
  }))), /*#__PURE__*/React.createElement("div", {
    className: "card"
  }, /*#__PURE__*/React.createElement("div", {
    className: "row",
    onClick: () => {
      haptic();
      setView('sources');
    }
  }, /*#__PURE__*/React.createElement("div", {
    className: "ic"
  }, /*#__PURE__*/React.createElement("i", {
    className: "ph ph-broadcast"
  })), /*#__PURE__*/React.createElement("div", {
    className: "body"
  }, /*#__PURE__*/React.createElement("div", {
    className: "title"
  }, "\u0418\u0441\u0442\u043E\u0447\u043D\u0438\u043A\u0438"), /*#__PURE__*/React.createElement("div", {
    className: "status"
  }, sources.length, " \u043F\u043E\u0434\u043A\u043B\u044E\u0447\u0435\u043D\u043E \xB7 \u043A\u0430\u043D\u0430\u043B\u044B \u0438 RSS")), /*#__PURE__*/React.createElement("div", {
    className: "chev"
  }, "\u203A"))), /*#__PURE__*/React.createElement("div", {
    className: "space-y-3.5"
  }, digestLoading && /*#__PURE__*/React.createElement("div", {
    className: "text-center py-8 text-xs text-slate-400"
  }, "\u0421\u043E\u0431\u0438\u0440\u0430\u0435\u043C \u0434\u0430\u0439\u0434\u0436\u0435\u0441\u0442\u2026"), digestError && !digestLoading && /*#__PURE__*/React.createElement("div", {
    className: "text-center py-6 text-xs text-red-500"
  }, digestError), !digestLoading && !digestError && digestData && /*#__PURE__*/React.createElement(React.Fragment, null, digestData.blocks && digestData.blocks.length > 0 ? digestData.blocks.map((block, bi) => /*#__PURE__*/React.createElement("div", {
    key: bi,
    className: "card"
  }, /*#__PURE__*/React.createElement("div", {
    className: "row",
    style: {
      paddingTop: 10,
      paddingBottom: 10
    }
  }, /*#__PURE__*/React.createElement("div", {
    className: "ic"
  }, /*#__PURE__*/React.createElement("i", {
    className: block.type === 'TG' ? 'ph ph-paper-plane-tilt' : 'ph ph-rss'
  })), /*#__PURE__*/React.createElement("div", {
    className: "body"
  }, /*#__PURE__*/React.createElement("div", {
    className: "title"
  }, block.title), /*#__PURE__*/React.createElement("div", {
    className: "status"
  }, block.posts.length, " \u043F\u043E\u0441\u0442\u043E\u0432 \u0437\u0430 3 \u0447\u0430\u0441\u0430")), /*#__PURE__*/React.createElement("div", {
    className: "chev"
  }, openPosts[bi] ? '▲' : '▼')), /*#__PURE__*/React.createElement("div", {
    className: "block space-y-2.5"
  }, block.summary && /*#__PURE__*/React.createElement("div", {
    className: "text-sm leading-relaxed whitespace-pre-wrap",
    style: {
      color: 'var(--text)'
    }
  }, block.summary), openPosts[bi] && /*#__PURE__*/React.createElement("div", {
    className: "space-y-1.5 pt-1"
  }, block.posts.map((p, pi) => /*#__PURE__*/React.createElement("div", {
    key: pi,
    className: "text-xs rounded-xl px-3 py-2",
    style: {
      background: 'var(--surface-subtle)',
      color: 'var(--text-muted)',
      lineHeight: 1.45
    }
  }, p))), /*#__PURE__*/React.createElement("button", {
    onClick: () => {
      haptic('light');
      setOpenPosts(s => ({
        ...s,
        [bi]: !s[bi]
      }));
    },
    className: "w-full py-2 rounded-xl font-bold text-xs transition active:scale-95",
    style: {
      background: 'var(--surface-subtle)',
      color: 'var(--accent)'
    }
  }, openPosts[bi] ? 'Скрыть посты' : 'Показать посты (' + block.posts.length + ')')))) : /*#__PURE__*/React.createElement("div", {
    className: "text-center py-8 text-xs text-slate-400"
  }, "\u0417\u0430 \u0432\u044B\u0431\u0440\u0430\u043D\u043D\u044B\u0439 \u043F\u0435\u0440\u0438\u043E\u0434 \u0441\u0432\u0435\u0436\u0438\u0445 \u043F\u043E\u0441\u0442\u043E\u0432 \u043D\u0435\u0442."), digestData.curs && /*#__PURE__*/React.createElement("div", {
    className: "card p-4 text-center"
  }, /*#__PURE__*/React.createElement("div", {
    className: "text-[10px] font-bold text-slate-400 uppercase tracking-wide mb-1"
  }, "\u041A\u0443\u0440\u0441 (\u0426\u0411)"), /*#__PURE__*/React.createElement("div", {
    className: "text-xs font-black text-slate-700"
  }, digestData.curs), /*#__PURE__*/React.createElement("div", {
    className: "text-[10px] text-slate-400 mt-1"
  }, "\u2B50 \u0412\u0441\u0435\u0433\u043E \u043F\u043E\u0441\u0442\u043E\u0432: ", digestData.total)))), /*#__PURE__*/React.createElement("button", {
    onClick: () => {
      haptic('light');
      loadDigest();
    },
    className: "w-full py-3 bg-slate-900 active:scale-98 text-white rounded-2xl font-bold text-xs transition"
  }, "\u041E\u0431\u043D\u043E\u0432\u0438\u0442\u044C \u0434\u0430\u0439\u0434\u0436\u0435\u0441\u0442")), auth.state === 'ok' && view === 'fun' && /*#__PURE__*/React.createElement("div", {
    className: "space-y-4 pb-24 animate-fade-in"
  }, /*#__PURE__*/React.createElement("div", {
    className: "header"
  }, /*#__PURE__*/React.createElement("div", {
    className: "btn",
    onClick: () => {
      haptic();
      setView('main');
    }
  }, /*#__PURE__*/React.createElement("i", {
    className: "ph ph-arrow-left"
  })), /*#__PURE__*/React.createElement("div", {
    className: "mid"
  }, /*#__PURE__*/React.createElement("div", {
    className: "title"
  }, "\u0412\u0438\u043A\u0442\u043E\u0440\u0438\u043D\u044B & \u0418\u0434\u0435\u0438"), /*#__PURE__*/React.createElement("div", {
    className: "subtitle"
  }, "\u0412\u043E\u043F\u0440\u043E\u0441\u044B \u0438 \u0437\u0430\u043D\u044F\u0442\u0438\u044F")), /*#__PURE__*/React.createElement("div", {
    className: "btn",
    onClick: () => {
      haptic('light');
      loadQuiz();
    }
  }, /*#__PURE__*/React.createElement("i", {
    className: "ph ph-shuffle"
  }))), /*#__PURE__*/React.createElement("div", {
    className: "card"
  }, /*#__PURE__*/React.createElement("div", {
    className: "row"
  }, /*#__PURE__*/React.createElement("div", {
    className: "ic acc"
  }, /*#__PURE__*/React.createElement("i", {
    className: "ph ph-brain"
  })), /*#__PURE__*/React.createElement("div", {
    className: "body"
  }, /*#__PURE__*/React.createElement("div", {
    className: "title"
  }, "\u0412\u043E\u043F\u0440\u043E\u0441 \u0434\u043B\u044F \u0432\u0438\u043A\u0442\u043E\u0440\u0438\u043D\u044B"), /*#__PURE__*/React.createElement("div", {
    className: "status"
  }, "Open Trivia DB")), /*#__PURE__*/React.createElement("button", {
    onClick: () => {
      haptic('light');
      loadQuiz();
    },
    disabled: quizLoading,
    className: "px-3 py-1.5 rounded-xl font-bold text-xs transition active:scale-95 disabled:opacity-50 text-white",
    style: {
      background: 'var(--accent)'
    }
  }, quizLoading ? '…' : 'Новый')), /*#__PURE__*/React.createElement("div", {
    className: "block space-y-3"
  }, quizError && /*#__PURE__*/React.createElement("div", {
    className: "text-xs font-bold px-3 py-2 rounded-xl",
    style: {
      color: '#EF4444',
      background: 'rgba(239,68,68,0.1)',
      border: '1px solid rgba(239,68,68,0.25)'
    }
  }, quizError), quizLoading && !quiz && /*#__PURE__*/React.createElement("div", {
    className: "text-center py-6 text-xs",
    style: {
      color: 'var(--text-muted)'
    }
  }, "\u0417\u0430\u0433\u0440\u0443\u0436\u0430\u0435\u043C \u0432\u043E\u043F\u0440\u043E\u0441\u2026"), quiz && !quizLoading && /*#__PURE__*/React.createElement("div", {
    className: "space-y-3"
  }, quiz.category && /*#__PURE__*/React.createElement("div", {
    className: "flex items-center gap-1.5 flex-wrap"
  }, /*#__PURE__*/React.createElement("span", {
    className: "px-2 py-0.5 rounded-lg text-[11px] font-bold",
    style: {
      color: 'var(--accent)',
      background: 'var(--accent-soft)'
    }
  }, quiz.category.title || 'Без категории'), quiz.value && /*#__PURE__*/React.createElement("span", {
    className: "px-2 py-0.5 rounded-lg text-[11px] font-bold",
    style: {
      color: '#D97706',
      background: 'rgba(245,158,11,0.12)'
    }
  }, "$", quiz.value)), /*#__PURE__*/React.createElement("div", {
    className: "text-sm font-bold leading-snug",
    style: {
      color: 'var(--text)'
    }
  }, quiz.question || '(вопрос не найден)'), !showAnswer ? /*#__PURE__*/React.createElement("button", {
    onClick: () => {
      haptic('medium');
      setShowAnswer(true);
    },
    className: "w-full py-3 rounded-2xl font-bold text-xs transition active:scale-95 text-white",
    style: {
      background: 'var(--text)'
    }
  }, "\u041F\u043E\u043A\u0430\u0437\u0430\u0442\u044C \u043E\u0442\u0432\u0435\u0442") : /*#__PURE__*/React.createElement("div", {
    className: "p-3.5 rounded-2xl",
    style: {
      background: 'rgba(16,185,129,0.08)',
      border: '1px solid rgba(16,185,129,0.25)'
    }
  }, /*#__PURE__*/React.createElement("div", {
    className: "text-[11px] font-bold uppercase tracking-wide mb-0.5",
    style: {
      color: '#10B981'
    }
  }, "\u041E\u0442\u0432\u0435\u0442"), /*#__PURE__*/React.createElement("div", {
    className: "text-sm font-bold",
    style: {
      color: 'var(--text)'
    }
  }, quiz.answer || '—')), quiz.airdate && /*#__PURE__*/React.createElement("div", {
    className: "text-[11px]",
    style: {
      color: 'var(--text-muted)'
    }
  }, "\u042D\u0444\u0438\u0440: ", new Date(quiz.airdate).toLocaleDateString('ru-RU'))))), /*#__PURE__*/React.createElement("div", {
    className: "card"
  }, /*#__PURE__*/React.createElement("div", {
    className: "row"
  }, /*#__PURE__*/React.createElement("div", {
    className: "ic"
  }, /*#__PURE__*/React.createElement("i", {
    className: "ph ph-lightbulb"
  })), /*#__PURE__*/React.createElement("div", {
    className: "body"
  }, /*#__PURE__*/React.createElement("div", {
    className: "title"
  }, "\u0427\u0435\u043C \u0437\u0430\u043D\u044F\u0442\u044C\u0441\u044F"), /*#__PURE__*/React.createElement("div", {
    className: "status"
  }, "BoredAPI")), /*#__PURE__*/React.createElement("button", {
    onClick: () => {
      haptic('light');
      loadActivity();
    },
    disabled: activityLoading,
    className: "px-3 py-1.5 rounded-xl font-bold text-xs transition active:scale-95 disabled:opacity-50 text-white",
    style: {
      background: 'var(--text)'
    }
  }, activityLoading ? '…' : 'Идея')), /*#__PURE__*/React.createElement("div", {
    className: "block space-y-3"
  }, activityError && /*#__PURE__*/React.createElement("div", {
    className: "text-xs font-bold px-3 py-2 rounded-xl",
    style: {
      color: '#EF4444',
      background: 'rgba(239,68,68,0.1)',
      border: '1px solid rgba(239,68,68,0.25)'
    }
  }, activityError), activityLoading && !activity && /*#__PURE__*/React.createElement("div", {
    className: "text-center py-6 text-xs",
    style: {
      color: 'var(--text-muted)'
    }
  }, "\u041F\u043E\u0434\u0431\u0438\u0440\u0430\u0435\u043C \u0437\u0430\u043D\u044F\u0442\u0438\u0435\u2026"), activity && !activityLoading && /*#__PURE__*/React.createElement("div", {
    className: "space-y-3"
  }, /*#__PURE__*/React.createElement("div", {
    className: "text-sm font-bold leading-snug",
    style: {
      color: 'var(--text)'
    }
  }, activity.activity), /*#__PURE__*/React.createElement("div", {
    className: "flex flex-wrap gap-1.5"
  }, /*#__PURE__*/React.createElement("span", {
    className: "px-2 py-0.5 rounded-lg text-[11px] font-bold capitalize",
    style: {
      color: '#8B5CF6',
      background: 'rgba(139,92,246,0.12)'
    }
  }, activity.type || 'разное'), activity.participants && /*#__PURE__*/React.createElement("span", {
    className: "px-2 py-0.5 rounded-lg text-[11px] font-bold",
    style: {
      color: 'var(--text-muted)',
      background: 'var(--surface-subtle)'
    }
  }, activity.participants, " ", activity.participants === 1 ? 'участник' : activity.participants < 5 ? 'участника' : 'участников'), priceLabel(activity.price) && /*#__PURE__*/React.createElement("span", {
    className: "px-2 py-0.5 rounded-lg text-[11px] font-bold",
    style: {
      color: '#059669',
      background: 'rgba(16,185,129,0.1)'
    }
  }, priceLabel(activity.price)), accessLabel(activity.accessibility) && /*#__PURE__*/React.createElement("span", {
    className: "px-2 py-0.5 rounded-lg text-[11px] font-bold",
    style: {
      color: '#D97706',
      background: 'rgba(245,158,11,0.12)'
    }
  }, accessLabel(activity.accessibility))), activity.link && /*#__PURE__*/React.createElement("a", {
    href: activity.link,
    target: "_blank",
    rel: "noopener noreferrer",
    className: "block text-center text-xs font-bold underline underline-offset-2",
    style: {
      color: 'var(--accent)'
    }
  }, "\u041F\u043E\u0434\u0440\u043E\u0431\u043D\u0435\u0435 \u2192")))), /*#__PURE__*/React.createElement("div", {
    className: "text-center text-[11px]",
    style: {
      color: 'var(--text-muted)'
    }
  }, "\u0414\u0430\u043D\u043D\u044B\u0435: Open Trivia DB \xB7 BoredAPI")), auth.state === 'ok' && view === 'translate' && /*#__PURE__*/React.createElement("div", {
    className: "space-y-4 pb-24 animate-fade-in"
  }, /*#__PURE__*/React.createElement("div", {
    className: "header"
  }, /*#__PURE__*/React.createElement("div", {
    className: "btn",
    onClick: () => {
      haptic();
      setView('main');
    }
  }, /*#__PURE__*/React.createElement("i", {
    className: "ph ph-arrow-left"
  })), /*#__PURE__*/React.createElement("div", {
    className: "mid"
  }, /*#__PURE__*/React.createElement("div", {
    className: "title"
  }, "\u041F\u0435\u0440\u0435\u0432\u043E\u0434\u0447\u0438\u043A"), /*#__PURE__*/React.createElement("div", {
    className: "subtitle"
  }, "\u0410\u043D\u0433\u043B\u0438\u0439\u0441\u043A\u0438\u0439 \u2194 \u0440\u0443\u0441\u0441\u043A\u0438\u0439 \xB7 \u0438\u0441\u043F\u0430\u043D\u0441\u043A\u0438\u0439 \u2194 \u0440\u0443\u0441\u0441\u043A\u0438\u0439")), /*#__PURE__*/React.createElement("div", {
    className: "btn",
    onClick: () => {
      haptic();
      setTrText('');
      setTrResult('');
      setTrError('');
    }
  }, /*#__PURE__*/React.createElement("i", {
    className: "ph ph-trash"
  }))), /*#__PURE__*/React.createElement("div", {
    className: "card p-1.5 flex gap-1"
  }, PAIRS.map(p => /*#__PURE__*/React.createElement("button", {
    key: p.id,
    onClick: () => {
      haptic('light');
      setTrPair(p.id);
      setTrResult('');
    },
    className: `flex-1 py-2.5 rounded-xl font-bold text-[11px] transition active:scale-95 ${trPair === p.id ? 'text-white' : ''}`,
    style: trPair === p.id ? {
      background: 'var(--accent)',
      color: '#fff'
    } : {
      color: 'var(--text-muted)',
      background: 'transparent'
    }
  }, p.label))), /*#__PURE__*/React.createElement("div", {
    className: "card p-4 space-y-3"
  }, /*#__PURE__*/React.createElement("textarea", {
    value: trText,
    onChange: e => setTrText(e.target.value),
    placeholder: "\u0412\u0441\u0442\u0430\u0432\u044C \u0442\u0435\u043A\u0441\u0442 \u0434\u043B\u044F \u043F\u0435\u0440\u0435\u0432\u043E\u0434\u0430\u2026",
    rows: "4",
    className: "w-full rounded-2xl p-3 text-sm resize-none outline-none border",
    style: {
      background: 'var(--surface-subtle)',
      borderColor: 'var(--border)',
      color: 'var(--text)'
    }
  }), /*#__PURE__*/React.createElement("div", {
    className: "flex gap-2"
  }, /*#__PURE__*/React.createElement("button", {
    onClick: () => {
      haptic('medium');
      doTranslate();
    },
    disabled: trLoading || !trText.trim(),
    className: "flex-1 py-3 rounded-2xl font-bold text-sm transition active:scale-95 disabled:opacity-40",
    style: {
      background: 'var(--accent)',
      color: '#fff'
    }
  }, trLoading ? '…' : 'Перевести'), /*#__PURE__*/React.createElement("button", {
    onClick: () => {
      haptic();
      setTrText('');
      setTrResult('');
      setTrError('');
    },
    className: "px-4 py-3 rounded-2xl font-bold text-sm transition active:scale-95",
    style: {
      background: 'var(--surface-subtle)',
      color: 'var(--text-muted)',
      border: '1px solid var(--border)'
    }
  }, /*#__PURE__*/React.createElement("i", {
    className: "ph ph-x"
  }))), trError && /*#__PURE__*/React.createElement("div", {
    className: "text-xs font-bold px-3 py-2 rounded-xl",
    style: {
      color: '#EF4444',
      background: 'rgba(239,68,68,0.1)',
      border: '1px solid rgba(239,68,68,0.25)'
    }
  }, trError), trResult && /*#__PURE__*/React.createElement("div", {
    className: "rounded-2xl p-3.5 space-y-2",
    style: {
      background: 'rgba(16,185,129,0.08)',
      border: '1px solid rgba(16,185,129,0.25)'
    }
  }, /*#__PURE__*/React.createElement("div", {
    className: "text-sm whitespace-pre-wrap break-words",
    style: {
      color: 'var(--text)'
    }
  }, trResult), /*#__PURE__*/React.createElement("div", {
    className: "flex items-center gap-3 pt-1"
  }, /*#__PURE__*/React.createElement("button", {
    onClick: () => {
      navigator.clipboard.writeText(trResult);
      haptic('notification');
      setTrCopied && setTrCopied(true);
      setTimeout(() => setTrCopied && setTrCopied(false), 2000);
    },
    className: "text-[11px] font-bold underline underline-offset-2",
    style: {
      color: '#10B981'
    }
  }, trCopied ? 'Скопировано ✓' : 'Копировать'), /*#__PURE__*/React.createElement("button", {
    onClick: () => {
      haptic('medium');
      addDict(trText, trResult);
    },
    className: "flex-1 py-2 rounded-xl font-bold text-xs transition active:scale-95 text-white",
    style: {
      background: '#10B981'
    }
  }, "\u0412 \u0441\u043B\u043E\u0432\u0430\u0440\u044C")))), /*#__PURE__*/React.createElement("div", {
    className: "card p-4 space-y-3"
  }, /*#__PURE__*/React.createElement("div", {
    className: "flex items-center justify-between"
  }, /*#__PURE__*/React.createElement("span", {
    className: "text-[11px] font-bold uppercase tracking-wide",
    style: {
      color: 'var(--text-muted)'
    }
  }, "\u0421\u043B\u043E\u0432\u0430\u0440\u044C (", dict.length, ")"), /*#__PURE__*/React.createElement("span", {
    className: "text-[10px]",
    style: {
      color: 'var(--text-muted)'
    }
  }, "\u0445\u0440\u0430\u043D\u0438\u0442\u0441\u044F \u043D\u0430 \u0443\u0441\u0442\u0440\u043E\u0439\u0441\u0442\u0432\u0435")), /*#__PURE__*/React.createElement("div", {
    className: "space-y-2"
  }, /*#__PURE__*/React.createElement("input", {
    value: dictSrc,
    onChange: e => setDictSrc(e.target.value),
    placeholder: "\u0424\u0440\u0430\u0437\u0430 (\u0430\u043D\u0433\u043B/\u0438\u0441\u043F)\u2026",
    className: "w-full rounded-xl px-3 py-2.5 text-sm outline-none border",
    style: {
      background: 'var(--surface-subtle)',
      borderColor: 'var(--border)',
      color: 'var(--text)'
    }
  }), /*#__PURE__*/React.createElement("input", {
    value: dictDst,
    onChange: e => setDictDst(e.target.value),
    placeholder: "\u041F\u0435\u0440\u0435\u0432\u043E\u0434 \u043D\u0430 \u0440\u0443\u0441\u0441\u043A\u0438\u0439\u2026",
    className: "w-full rounded-xl px-3 py-2.5 text-sm outline-none border",
    style: {
      background: 'var(--surface-subtle)',
      borderColor: 'var(--border)',
      color: 'var(--text)'
    }
  }), /*#__PURE__*/React.createElement("button", {
    onClick: () => {
      haptic('medium');
      addDict(dictSrc, dictDst);
      setDictSrc('');
      setDictDst('');
    },
    disabled: !dictSrc.trim(),
    className: "w-full py-2.5 rounded-xl font-bold text-xs transition active:scale-95 text-white disabled:opacity-40",
    style: {
      background: 'var(--text)'
    }
  }, "\u0414\u043E\u0431\u0430\u0432\u0438\u0442\u044C \u0432 \u0441\u043B\u043E\u0432\u0430\u0440\u044C")), dict.length === 0 ? /*#__PURE__*/React.createElement("div", {
    className: "text-xs rounded-xl px-3 py-4 text-center",
    style: {
      color: 'var(--text-muted)',
      background: 'var(--surface-subtle)'
    }
  }, "\u0421\u043B\u043E\u0432\u0430\u0440\u044C \u043F\u0443\u0441\u0442. \u0414\u043E\u0431\u0430\u0432\u044C \u0444\u0440\u0430\u0437\u0443 \u0441 \u043F\u0435\u0440\u0435\u0432\u043E\u0434\u043E\u043C \u0438\u043B\u0438 \u0441\u043E\u0445\u0440\u0430\u043D\u0438 \u043F\u0435\u0440\u0435\u0432\u043E\u0434 \u043A\u043D\u043E\u043F\u043A\u043E\u0439 \xAB\u0412 \u0441\u043B\u043E\u0432\u0430\u0440\u044C\xBB.") : /*#__PURE__*/React.createElement("div", {
    className: "space-y-2 max-h-72 overflow-y-auto"
  }, dict.map(x => /*#__PURE__*/React.createElement("div", {
    key: x.id,
    className: "rounded-xl px-3 py-2.5 space-y-0.5",
    style: {
      background: 'var(--surface-subtle)',
      border: '1px solid var(--border)'
    }
  }, /*#__PURE__*/React.createElement("div", {
    className: "flex items-start justify-between gap-2"
  }, /*#__PURE__*/React.createElement("div", {
    className: "text-sm font-bold break-words",
    style: {
      color: 'var(--text)'
    }
  }, x.src), /*#__PURE__*/React.createElement("button", {
    onClick: () => {
      haptic('light');
      removeDict(x.id);
    },
    className: "text-sm shrink-0",
    style: {
      color: 'var(--text-muted)'
    }
  }, /*#__PURE__*/React.createElement("i", {
    className: "ph ph-x"
  }))), x.dst && /*#__PURE__*/React.createElement("div", {
    className: "text-xs break-words",
    style: {
      color: 'var(--text-muted)'
    }
  }, "\uD83C\uDDF7\uD83C\uDDFA ", x.dst))))), /*#__PURE__*/React.createElement("div", {
    className: "text-center text-[10px]",
    style: {
      color: 'var(--text-muted)'
    }
  }, "\u041F\u0435\u0440\u0435\u0432\u043E\u0434: MyMemory API \xB7 \u043B\u0438\u043C\u0438\u0442 ~50K \u0441\u0438\u043C\u0432\u043E\u043B\u043E\u0432/\u0434\u0435\u043D\u044C")));
}
function AdminPanel({
  auth,
  apiFetch,
  haptic,
  onBack
}) {
  const [users, setUsers] = useState([]);
  const [audit, setAudit] = useState([]);
  const [err, setErr] = useState('');
  const [busy, setBusy] = useState(false);
  const load = () => {
    Promise.all([apiFetch('/miniapp/api/admin/users').then(r => r.json()), apiFetch('/miniapp/api/admin/audit').then(r => r.json())]).then(([u, a]) => {
      if (u.ok) setUsers(u.users || []);
      if (a.ok) setAudit(a.audit || []);
    }).catch(() => setErr('Не удалось загрузить админ-данные'));
  };
  useEffect(() => {
    load();
  }, []);
  const updateUser = (tgId, patch) => {
    setBusy(true);
    setErr('');
    apiFetch('/miniapp/api/admin/users', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        telegram_id: tgId,
        ...patch
      })
    }).then(r => r.json()).then(d => {
      if (d.ok) setUsers(d.users);else setErr(d.error || 'Ошибка');
    }).catch(() => setErr('Сервер недоступен')).finally(() => setBusy(false));
  };
  const deleteUser = tgId => {
    if (!confirm('Удалить пользователя?')) return;
    setBusy(true);
    setErr('');
    apiFetch('/miniapp/api/admin/users?telegram_id=' + tgId, {
      method: 'DELETE'
    }).then(r => r.json()).then(d => {
      if (d.ok) setUsers(d.users);else setErr(d.error || 'Ошибка');
    }).catch(() => setErr('Сервер недоступен')).finally(() => setBusy(false));
  };
  return /*#__PURE__*/React.createElement("div", {
    className: "space-y-4 animate-fade-in pb-24"
  }, /*#__PURE__*/React.createElement("div", {
    className: "flex items-center justify-between"
  }, /*#__PURE__*/React.createElement("button", {
    onClick: () => {
      haptic();
      onBack();
    },
    className: "px-3.5 py-2 bg-slate-100 border border-slate-200 text-slate-700 font-bold rounded-xl text-xs transition active:scale-95"
  }, "\u2190 \u041D\u0430\u0437\u0430\u0434"), /*#__PURE__*/React.createElement("span", {
    className: "text-xs font-black text-purple-600 bg-purple-50 px-2.5 py-1 rounded-lg border border-purple-200"
  }, "\u0410\u0434\u043C\u0438\u043D-\u043F\u0430\u043D\u0435\u043B\u044C"), /*#__PURE__*/React.createElement("button", {
    onClick: () => {
      haptic('light');
      load();
    },
    className: "text-xs font-bold text-slate-500 px-2 py-1"
  }, "\uD83D\uDD04")), err && /*#__PURE__*/React.createElement("div", {
    className: "text-xs font-bold text-red-500 bg-red-50 border border-red-200 rounded-xl px-3 py-2"
  }, err), /*#__PURE__*/React.createElement("div", {
    className: "card p-4 space-y-2"
  }, /*#__PURE__*/React.createElement("div", {
    className: "text-[11px] font-bold text-slate-400 uppercase tracking-wide mb-1"
  }, "\u041F\u043E\u043B\u044C\u0437\u043E\u0432\u0430\u0442\u0435\u043B\u0438"), users.map(u => /*#__PURE__*/React.createElement("div", {
    key: u.telegram_id,
    className: "flex items-center justify-between gap-2 p-2.5 bg-slate-50 rounded-xl border border-slate-200"
  }, /*#__PURE__*/React.createElement("div", {
    className: "min-w-0"
  }, /*#__PURE__*/React.createElement("div", {
    className: "text-xs font-bold text-slate-800 truncate"
  }, u.first_name || u.username || 'id ' + u.telegram_id, u.telegram_id === auth.user.telegram_id && /*#__PURE__*/React.createElement("span", {
    className: "text-blue-500"
  }, " (\u0432\u044B)")), /*#__PURE__*/React.createElement("div", {
    className: "text-[10px] text-slate-400 truncate"
  }, "@", u.username || '—', " \xB7 tg:", u.telegram_id)), /*#__PURE__*/React.createElement("div", {
    className: "flex items-center gap-1.5 shrink-0"
  }, /*#__PURE__*/React.createElement("select", {
    value: u.role,
    disabled: u.telegram_id === auth.user.telegram_id || busy,
    onChange: e => updateUser(u.telegram_id, {
      role: e.target.value
    }),
    className: "text-[10px] font-bold bg-white border border-slate-200 rounded-lg px-1.5 py-1"
  }, /*#__PURE__*/React.createElement("option", {
    value: "user"
  }, "user"), /*#__PURE__*/React.createElement("option", {
    value: "admin"
  }, "admin")), /*#__PURE__*/React.createElement("button", {
    onClick: () => updateUser(u.telegram_id, {
      allowed: u.allowed ? false : true
    }),
    disabled: u.telegram_id === auth.user.telegram_id || busy,
    className: `text-[10px] font-bold px-2 py-1 rounded-lg border ${u.allowed ? 'bg-emerald-50 text-emerald-600 border-emerald-200' : 'bg-red-50 text-red-500 border-red-200'}`
  }, u.allowed ? 'Доступ ✓' : 'Заблок.'), u.telegram_id !== auth.user.telegram_id && /*#__PURE__*/React.createElement("button", {
    onClick: () => deleteUser(u.telegram_id),
    disabled: busy,
    className: "text-[10px] font-bold text-slate-400 hover:text-red-500 px-1.5 py-1"
  }, "\xD7")))), users.length === 0 && /*#__PURE__*/React.createElement("div", {
    className: "text-center py-3 text-xs text-slate-400"
  }, "\u041F\u043E\u043B\u044C\u0437\u043E\u0432\u0430\u0442\u0435\u043B\u0435\u0439 \u043D\u0435\u0442")), /*#__PURE__*/React.createElement("div", {
    className: "card p-4 space-y-1.5"
  }, /*#__PURE__*/React.createElement("div", {
    className: "text-[11px] font-bold text-slate-400 uppercase tracking-wide mb-1"
  }, "\u0410\u0443\u0434\u0438\u0442 \u0432\u0445\u043E\u0434\u043E\u0432 (\u043F\u043E\u0441\u043B\u0435\u0434\u043D\u0438\u0435 50)"), audit.map((a, i) => /*#__PURE__*/React.createElement("div", {
    key: i,
    className: "flex items-center justify-between gap-2 text-[10px]"
  }, /*#__PURE__*/React.createElement("span", {
    className: "text-slate-500 font-mono"
  }, new Date(a.ts * 1000).toLocaleString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })), /*#__PURE__*/React.createElement("span", {
    className: "text-slate-400"
  }, "tg:", a.telegram_id), /*#__PURE__*/React.createElement("span", {
    className: "font-bold text-slate-600"
  }, a.action))), audit.length === 0 && /*#__PURE__*/React.createElement("div", {
    className: "text-center py-2 text-xs text-slate-400"
  }, "\u0421\u043E\u0431\u044B\u0442\u0438\u0439 \u043D\u0435\u0442")));
}
ReactDOM.createRoot(document.getElementById('root')).render(/*#__PURE__*/React.createElement(App, null));
