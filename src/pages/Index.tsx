import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import Icon from '@/components/ui/icon';
import { useToast } from '@/hooks/use-toast';

const API_URL = 'https://functions.poehali.dev/29ec2cf8-be14-47c7-9bd8-1965dae40fb3';
const WEBHOOK_SETUP_URL = 'https://functions.poehali.dev/d22da8d2-66f4-4d1b-8a19-e14bcb758144';
const ADMIN_USERNAME = 'skzry';

interface Certificate {
  id: string;
  owner_name: string;
  certificate_url: string;
  status: 'valid' | 'invalid';
  valid_from?: string;
  valid_until?: string;
  created_at: string;
}

const Index = () => {
  const [certificates, setCertificates] = useState<Certificate[]>([]);
  const [showAddForm, setShowAddForm] = useState(false);
  const [newCert, setNewCert] = useState({ id: '', owner_name: '', certificate_url: '', status: 'valid' as 'valid' | 'invalid', valid_from: '', valid_until: '' });
  const [editingCert, setEditingCert] = useState<Certificate | null>(null);
  const [loading, setLoading] = useState(false);
  const [webhookStatus, setWebhookStatus] = useState<string>('');
  const { toast } = useToast();

  useEffect(() => {
    fetchCertificates();
    checkWebhook();
  }, []);

  const fetchCertificates = async () => {
    try {
      const res = await fetch(API_URL);
      const data = await res.json();
      setCertificates(data.certificates || []);
    } catch (error) {
      console.error('Ошибка загрузки:', error);
    }
  };

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
        setNewCert({ id: '', owner_name: '', certificate_url: '', status: 'valid', valid_from: '', valid_until: '' });
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

  const handleStatusChange = async (id: string, newStatus: 'valid' | 'invalid') => {
    try {
      const res = await fetch(API_URL, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'X-Admin-Token': ADMIN_USERNAME
        },
        body: JSON.stringify({ id, status: newStatus })
      });

      if (res.ok) {
        toast({ title: '✅ Статус обновлен' });
        fetchCertificates();
      } else {
        const data = await res.json();
        toast({ title: data.error || 'Ошибка обновления', variant: 'destructive' });
      }
    } catch (error) {
      toast({ title: 'Ошибка сети', variant: 'destructive' });
    }
  };

  const handleEdit = async () => {
    if (!editingCert) return;

    setLoading(true);
    try {
      const res = await fetch(API_URL, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'X-Admin-Token': ADMIN_USERNAME
        },
        body: JSON.stringify(editingCert)
      });

      if (res.ok) {
        toast({ title: '✅ Сертификат обновлен!' });
        setEditingCert(null);
        fetchCertificates();
      } else {
        const data = await res.json();
        toast({ title: data.error || 'Ошибка обновления', variant: 'destructive' });
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
      <div className="container mx-auto px-4 py-8 max-w-7xl">
        <div className="text-center mb-8 animate-fade-in">
          <div className="flex items-center justify-center gap-3 mb-4">
            <Icon name="ShieldCheck" size={48} className="text-primary" />
            <h1 className="text-5xl font-bold bg-gradient-to-r from-primary via-accent to-secondary bg-clip-text text-transparent">
              Админ-панель
            </h1>
          </div>
          <p className="text-lg text-muted-foreground">Управление сертификатами для @{ADMIN_USERNAME}</p>
        </div>

        <div className="grid gap-6 md:grid-cols-2 mb-8">
          <Card className="shadow-lg hover-scale transition-all border-2">
            <CardHeader className="bg-gradient-to-r from-primary/10 to-accent/10">
              <CardTitle className="flex items-center gap-2">
                <Icon name="Plus" size={24} />
                Добавить Сертификат
              </CardTitle>
              <CardDescription>Создание нового сертификата</CardDescription>
            </CardHeader>
            <CardContent className="pt-6">
              {!showAddForm ? (
                <Button onClick={() => setShowAddForm(true)} className="w-full gap-2" size="lg">
                  <Icon name="Plus" size={20} />
                  Создать Сертификат
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
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="text-xs text-muted-foreground mb-1 block">Действителен с</label>
                      <Input
                        type="date"
                        value={newCert.valid_from}
                        onChange={(e) => setNewCert({ ...newCert, valid_from: e.target.value })}
                      />
                    </div>
                    <div>
                      <label className="text-xs text-muted-foreground mb-1 block">Действителен до</label>
                      <Input
                        type="date"
                        value={newCert.valid_until}
                        onChange={(e) => setNewCert({ ...newCert, valid_until: e.target.value })}
                      />
                    </div>
                  </div>
                  <Select value={newCert.status} onValueChange={(v: 'valid' | 'invalid') => setNewCert({ ...newCert, status: v })}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="valid">✅ Действительно</SelectItem>
                      <SelectItem value="invalid">❌ Недействительно</SelectItem>
                    </SelectContent>
                  </Select>
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

          <Card className="shadow-lg hover-scale transition-all border-2">
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
              <CardDescription>Статус интеграции</CardDescription>
            </CardHeader>
            <CardContent className="pt-6 space-y-3">
              <div className="flex gap-2">
                <Button 
                  onClick={setupWebhook} 
                  disabled={loading}
                  className="flex-1 gap-2"
                >
                  <Icon name="Play" size={18} />
                  {webhookStatus.includes('✅') ? 'Переподключить' : 'Подключить'}
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
              <div className="p-3 bg-blue-50 rounded-lg border border-blue-200 text-sm text-blue-800">
                <p><strong>💡 Как проверить:</strong> Отправьте /start боту в Telegram</p>
              </div>
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
                  className="p-4 rounded-lg bg-gradient-to-r from-muted/50 to-muted/30 hover:from-muted hover:to-muted/50 transition-all border animate-fade-in"
                  style={{ animationDelay: `${idx * 0.05}s` }}
                >
                  {editingCert?.id === cert.id ? (
                    <div className="space-y-3">
                      <Input
                        placeholder="Кому принадлежит"
                        value={editingCert.owner_name}
                        onChange={(e) => setEditingCert({ ...editingCert, owner_name: e.target.value })}
                      />
                      <Input
                        placeholder="Ссылка на сертификат"
                        value={editingCert.certificate_url}
                        onChange={(e) => setEditingCert({ ...editingCert, certificate_url: e.target.value })}
                      />
                      <div className="grid grid-cols-2 gap-2">
                        <div>
                          <label className="text-xs text-muted-foreground mb-1 block">Действителен с</label>
                          <Input
                            type="date"
                            value={editingCert.valid_from || ''}
                            onChange={(e) => setEditingCert({ ...editingCert, valid_from: e.target.value })}
                          />
                        </div>
                        <div>
                          <label className="text-xs text-muted-foreground mb-1 block">Действителен до</label>
                          <Input
                            type="date"
                            value={editingCert.valid_until || ''}
                            onChange={(e) => setEditingCert({ ...editingCert, valid_until: e.target.value })}
                          />
                        </div>
                      </div>
                      <Select 
                        value={editingCert.status} 
                        onValueChange={(v: 'valid' | 'invalid') => setEditingCert({ ...editingCert, status: v })}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="valid">✅ Действительно</SelectItem>
                          <SelectItem value="invalid">❌ Недействительно</SelectItem>
                        </SelectContent>
                      </Select>
                      <div className="flex gap-2">
                        <Button onClick={handleEdit} disabled={loading} className="flex-1 gap-2">
                          <Icon name="Save" size={18} />
                          Сохранить
                        </Button>
                        <Button onClick={() => setEditingCert(null)} variant="outline">
                          Отмена
                        </Button>
                      </div>
                    </div>
                  ) : (
                    <div className="flex items-start gap-4">
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
                        {(cert.valid_from || cert.valid_until) && (
                          <div className="text-xs text-muted-foreground mt-2 space-y-1">
                            {cert.valid_from && <div>📅 С: {cert.valid_from}</div>}
                            {cert.valid_until && <div>📅 До: {cert.valid_until}</div>}
                          </div>
                        )}
                      </div>
                      <div className="flex items-center gap-2">
                        <Select 
                          value={cert.status} 
                          onValueChange={(v: 'valid' | 'invalid') => handleStatusChange(cert.id, v)}
                        >
                          <SelectTrigger className="w-[180px]">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="valid">✅ Действительно</SelectItem>
                            <SelectItem value="invalid">❌ Недействительно</SelectItem>
                          </SelectContent>
                        </Select>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => setEditingCert(cert)}
                          className="text-primary hover:text-primary"
                        >
                          <Icon name="Pencil" size={18} />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => handleDelete(cert.id)}
                          className="text-destructive hover:text-destructive"
                        >
                          <Icon name="Trash2" size={18} />
                        </Button>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Index;