import React, { useEffect, useState } from 'react';
import { useSearchParams, Link } from 'react-router-dom';

const VerifyEmail: React.FC = () => {
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token');
  const [status, setStatus] = useState<'verifying' | 'success' | 'error'>('verifying');
  const [message, setMessage] = useState('');

  useEffect(() => {
    if (token) {
      verifyToken(token);
    } else {
      setStatus('error');
      setMessage('No token provided.');
    }
  }, [token]);

  const verifyToken = async (token: string) => {
    try {
      const response = await fetch(`http://localhost:8000/auth/verify/${token}`);
      const data = await response.json();
      if (response.ok) {
        setStatus('success');
        setMessage(data.message);
      } else {
        setStatus('error');
        setMessage(data.detail || 'Verification failed');
      }
    } catch (error) {
      setStatus('error');
      setMessage('An error occurred during verification.');
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-100">
      <div className="p-8 bg-white rounded shadow-md w-96 text-center">
        <h2 className="mb-6 text-2xl font-bold">Email Verification</h2>
        {status === 'verifying' && <p>Verifying your email...</p>}
        {status === 'success' && (
          <div>
            <p className="text-green-500 mb-4">{message}</p>
            <Link to="/login" className="text-blue-500 underline">Go to Login</Link>
          </div>
        )}
        {status === 'error' && (
          <div>
            <p className="text-red-500 mb-4">{message}</p>
            <Link to="/login" className="text-blue-500 underline">Go to Login</Link>
          </div>
        )}
      </div>
    </div>
  );
};

export default VerifyEmail;
