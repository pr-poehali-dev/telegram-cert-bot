import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import Icon from '@/components/ui/icon';
import { useToast } from '@/hooks/use-toast';

const API_URL = 'https://functions.poehali.dev/29ec2cf8-be14-47c7-9bd8-1965dae40fb3';
const WEBHOOK_SETUP_URL = 'https://functions.poehali.dev/d22da8d2-66f4-4d1b-8a19-e14bcb758144';
const ADMIN_USERNAME = 'skzry';

interface Certificate {
  id: string;
  owner_name: string;
  certificate_url: string;
  created_at: string;
}

const Index = () => {
  const [certificates, setCertificates] = useState<Certificate[]>([]);
  const [searchId, setSearchId] = useState('');
  const [searchResult, setSearchResult] = useState<Certificate | null>(null);
  const [showAddForm, setShowAddForm] = useState(false);
  const [newCert, setNewCert] = useState({ id: '', owner_name: '', certificate_url: '' });
  const [loading, setLoading] = useState(false);
  const [webhookStatus, setWebhookStatus] = useState<string>('');
  const { toast } = useToast();

  useEffect(() => {
    fetchCertificates();
    checkWebhook();
  }, []);

  const checkWebhook = async () => {
    try {
      const res = await fetch(WEBHOOK_SETUP_URL);
      const data = await res.json();
      if (data.result?.url) {
        setWebhookStatus('✅ Активен');
      } else {
        setWebhookStatus('⚠️ Не настроен');
      }
    } catch (error) {
      setWebhookStatus('❌ Ошибка');
    }
  };

  const setupWebhook = async () => {
    setLoading(true);
    try {
      const res = await fetch(WEBHOOK_SETUP_URL, { method: 'POST' });
      const data = await res.json();
      if (data.ok) {
        toast({ title: '✅ Webhook настроен!' });
        checkWebhook();
      } else {
        toast({ title: 'Ошибка настройки webhook', variant: 'destructive' });
      }
    } catch (error) {
      toast({ title: 'Ошибка сети', variant: 'destructive' });
    } finally {
      setLoading(false);
    }
  };

  const fetchCertificates = async () => {
    try {
      const res = await fetch(API_URL);
      const data = await res.json();
      setCertificates(data.certificates || []);
    } catch (error) {
      console.error('Ошибка загрузки:', error);
    }
  };

  const handleSearch = async () => {
    if (!searchId.trim()) {
      toast({ title: 'Введите ID сертификата', variant: 'destructive' });
      return;
    }
    
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}?id=${encodeURIComponent(searchId.trim())}`);
      const data = await res.json();
      
      if (data.found) {
        setSearchResult(data.certificate);
        toast({ title: '✅ Сертификат найден!' });
      } else {
        setSearchResult(null);
        toast({ title: '❌ Сертификат не найден', variant: 'destructive' });
      }
    } catch (error) {
      toast({ title: 'Ошибка поиска', variant: 'destructive' });
    } finally {
      setLoading(false);
    }
  };

  const handleAdd = async () => {
    if (!newCert.id || !newCert.owner_name || !newCert.certificate_url) {
      toast({ title: 'Заполните все поля', variant: 'destructive' });
      return;
    }

    setLoading(true);
    try {
      const res = await fetch(API_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Admin-Token': ADMIN_USERNAME
        },
        body: JSON.stringify(newCert)
      });

      const data = await res.json();
      
      if (res.ok) {
        toast({ title: '✅ Сертификат добавлен!' });
        setNewCert({ id: '', owner_name: '', certificate_url: '' });
        setShowAddForm(false);
        fetchCertificates();
      } else {
        toast({ title: data.error || 'Ошибка добавления', variant: 'destructive' });
      }
    } catch (error) {
      toast({ title: 'Ошибка сети', variant: 'destructive' });
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Удалить сертификат?')) return;

    try {
      const res = await fetch(`${API_URL}?id=${encodeURIComponent(id)}`, {
        method: 'DELETE',
        headers: { 'X-Admin-Token': ADMIN_USERNAME }
      });

      if (res.ok) {
        toast({ title: '✅ Сертификат удален' });
        fetchCertificates();
        if (searchResult?.id === id) setSearchResult(null);
      } else {
        const data = await res.json();
        toast({ title: data.error || 'Ошибка удаления', variant: 'destructive' });
      }
    } catch (error) {
      toast({ title: 'Ошибка сети', variant: 'destructive' });
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-pink-50 to-blue-50">
      <div className="container mx-auto px-4 py-8 max-w-6xl">
        <div className="text-center mb-8 animate-fade-in">
          <div className="flex items-center justify-center gap-3 mb-4">
            <Icon name="ShieldCheck" size={48} className="text-primary" />
            <h1 className="text-5xl font-bold bg-gradient-to-r from-primary via-accent to-secondary bg-clip-text text-transparent">
              Верификация Сертификатов
            </h1>
          </div>
          <p className="text-lg text-muted-foreground">Система поиска и управления сертификатами</p>
        </div>

        <div className="grid gap-6 md:grid-cols-2 mb-8">
          <Card className="shadow-lg hover-scale transition-all border-2">
            <CardHeader className="bg-gradient-to-r from-primary/10 to-accent/10">
              <CardTitle className="flex items-center gap-2">
                <Icon name="Search" size={24} />
                Поиск Сертификата
              </CardTitle>
              <CardDescription>Введите ID для проверки</CardDescription>
            </CardHeader>
            <CardContent className="pt-6">
              <div className="flex gap-2 mb-4">
                <Input
                  placeholder="CERT-2024-001"
                  value={searchId}
                  onChange={(e) => setSearchId(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                  className="flex-1"
                />
                <Button onClick={handleSearch} disabled={loading} className="gap-2">
                  <Icon name="Search" size={18} />
                  Найти
                </Button>
              </div>

              {searchResult && (
                <div className="p-4 rounded-lg bg-gradient-to-r from-green-50 to-emerald-50 border-2 border-green-200 animate-scale-in">
                  <div className="flex items-start gap-3 mb-3">
                    <Icon name="CheckCircle2" size={24} className="text-green-600 mt-1" />
                    <div className="flex-1">
                      <Badge className="mb-2 bg-green-600">{searchResult.id}</Badge>
                      <p className="font-semibold text-lg text-green-900">{searchResult.owner_name}</p>
                    </div>
                  </div>
                  <a
                    href={searchResult.certificate_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-2 text-primary hover:underline font-medium"
                  >
                    <Icon name="ExternalLink" size={16} />
                    Открыть сертификат
                  </a>
                </div>
              )}
            </CardContent>
          </Card>

          <Card className="shadow-lg hover-scale transition-all border-2">
            <CardHeader className="bg-gradient-to-r from-secondary/10 to-primary/10">
              <CardTitle className="flex items-center gap-2">
                <Icon name="Shield" size={24} />
                Админ-панель
              </CardTitle>
              <CardDescription>Только для @{ADMIN_USERNAME}</CardDescription>
            </CardHeader>
            <CardContent className="pt-6">
              {!showAddForm ? (
                <Button onClick={() => setShowAddForm(true)} className="w-full gap-2" size="lg">
                  <Icon name="Plus" size={20} />
                  Добавить Сертификат
                </Button>
              ) : (
                <div className="space-y-3 animate-fade-in">
                  <Input
                    placeholder="ID сертификата"
                    value={newCert.id}
                    onChange={(e) => setNewCert({ ...newCert, id: e.target.value })}
                  />
                  <Input
                    placeholder="Кому принадлежит"
                    value={newCert.owner_name}
                    onChange={(e) => setNewCert({ ...newCert, owner_name: e.target.value })}
                  />
                  <Input
                    placeholder="Ссылка на сертификат"
                    value={newCert.certificate_url}
                    onChange={(e) => setNewCert({ ...newCert, certificate_url: e.target.value })}
                  />
                  <div className="flex gap-2">
                    <Button onClick={handleAdd} disabled={loading} className="flex-1 gap-2">
                      <Icon name="Save" size={18} />
                      Сохранить
                    </Button>
                    <Button onClick={() => setShowAddForm(false)} variant="outline">
                      Отмена
                    </Button>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        <Card className="shadow-xl border-2">
          <CardHeader className="bg-gradient-to-r from-primary/5 to-accent/5">
            <CardTitle className="flex items-center gap-2">
              <Icon name="Database" size={24} />
              Все Сертификаты ({certificates.length})
            </CardTitle>
            <CardDescription>База сертификатов в системе</CardDescription>
          </CardHeader>
          <CardContent className="pt-6">
            <div className="space-y-3">
              {certificates.map((cert, idx) => (
                <div
                  key={cert.id}
                  className="flex items-center justify-between p-4 rounded-lg bg-gradient-to-r from-muted/50 to-muted/30 hover:from-muted hover:to-muted/50 transition-all border animate-fade-in"
                  style={{ animationDelay: `${idx * 0.05}s` }}
                >
                  <div className="flex-1">
                    <Badge variant="outline" className="mb-2">{cert.id}</Badge>
                    <p className="font-semibold">{cert.owner_name}</p>
                    <a
                      href={cert.certificate_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-sm text-primary hover:underline flex items-center gap-1 mt-1"
                    >
                      <Icon name="Link" size={14} />
                      {cert.certificate_url}
                    </a>
                  </div>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => handleDelete(cert.id)}
                    className="text-destructive hover:text-destructive"
                  >
                    <Icon name="Trash2" size={18} />
                  </Button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card className="mt-8 shadow-xl border-2">
          <CardHeader className="bg-gradient-to-r from-primary/10 via-accent/10 to-secondary/10">
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <Icon name="MessageSquare" size={24} className="text-primary" />
                Telegram-бот
              </CardTitle>
              <Badge variant={webhookStatus.includes('✅') ? 'default' : 'secondary'}>
                {webhookStatus || 'Проверка...'}
              </Badge>
            </div>
            <CardDescription>Интеграция с Telegram Bot API</CardDescription>
          </CardHeader>
          <CardContent className="pt-6 space-y-4">
            <div>
              <p className="text-sm font-semibold mb-2">🔗 Webhook URL:</p>
              <code className="block p-3 bg-muted rounded text-xs font-mono break-all">
                https://functions.poehali.dev/5c3b7278-e9ff-4484-9925-98c58472a712
              </code>
            </div>

            <div className="flex gap-2">
              <Button 
                onClick={setupWebhook} 
                disabled={loading}
                className="gap-2"
              >
                <Icon name="Play" size={18} />
                {webhookStatus.includes('✅') ? 'Переподключить' : 'Подключить'} Webhook
              </Button>
              <Button 
                onClick={checkWebhook} 
                variant="outline"
                className="gap-2"
              >
                <Icon name="RefreshCw" size={18} />
                Проверить
              </Button>
            </div>

            <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
              <p className="text-sm font-semibold mb-2 text-blue-900">💡 Как пользоваться:</p>
              <ol className="text-sm text-blue-800 space-y-1 list-decimal list-inside">
                <li>Найдите вашего бота в Telegram</li>
                <li>Отправьте команду <code className="bg-blue-100 px-1 rounded">/start</code></li>
                <li>Введите ID сертификата (например: CERT-2024-001)</li>
                <li>Получите информацию и ссылку на сертификат!</li>
              </ol>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Index;